#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import tempfile
import os
import responses
import requests
import requests_cache
import logging
import socket

import ruamel.yaml
from github import GithubException, UnknownObjectException, RateLimitExceededException

from lfx_landscape_tools.config import Config
from lfx_landscape_tools.cli import Cli
from lfx_landscape_tools.member import Member
from lfx_landscape_tools.members import Members
from lfx_landscape_tools.lfxmembers import LFXMembers
from lfx_landscape_tools.landscapemembers import LandscapeMembers
from lfx_landscape_tools.landscapeoutput import LandscapeOutput
from lfx_landscape_tools.svglogo import SVGLogo
from lfx_landscape_tools.lfxprojects import LFXProjects
from lfx_landscape_tools.tacagendaproject import TACAgendaProject

class TestMember(unittest.TestCase):

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("debug.log",mode="w"),
        ]
    )

    def setUp(self):
        logging.getLogger().debug("Running {}".format(unittest.TestCase.id(self)))
        requests_cache.uninstall_cache()
        with open("{}/data.yml".format(os.path.dirname(__file__)), 'r', encoding="utf8", errors='ignore') as fileobject:
            responses.get('https://raw.githubusercontent.com/cncf/landscape2/refs/heads/main/docs/config/data.yml', body=fileobject.read())
        with open("{}/github_openassetio_response.html".format(os.path.dirname(__file__)), 'r', encoding="utf8", errors='ignore') as fileobject:
            responses.get("https://github.com/OpenAssetIO",body=fileobject.read())
        with open("{}/github_openassetio_search_repo.json".format(os.path.dirname(__file__)), 'r', encoding="utf8", errors='ignore') as fileobject:
            responses.get("https://api.github.com:443/search/repositories?sort=stars&order=desc&q=org%3AOpenAssetIO&per_page=1000",body=fileobject.read())

    def testLinkedInValid(self):
        validLinkedInURLs = [
            'https://www.linkedin.com/company/1nce',
            'company/1nce',
            'https://linkedin.com/company/1nce',
        ]

        for validLinkedInURL in validLinkedInURLs:
            member = Member()
            member.linkedin = validLinkedInURL
            self.assertEqual(member.linkedin,'https://www.linkedin.com/company/1nce')
            self.assertEqual(member.toLandscapeItemAttributes().get('organization',{}).get('linkedin'),'https://www.linkedin.com/company/1nce')

    def testSetLinkedInNotValidOnEmpty(self):
        member = Member()
        member.name = 'test'
        member.linkedin = ''
        self.assertIsNone(member.linkedin)

    def testSetLinkedNotValid(self):
        invalidLinkedInURLs = [
            'https://yahoo.com',
            'https://www.crunchbase.com/person/johndoe'
        ]

        for invalidLinkedInURL in invalidLinkedInURLs:
            member = Member()
            member.name = 'test'
            with self.assertLogs() as cm:
                member.linkedin = invalidLinkedInURL
                self.assertEqual(["WARNING:root:Member.linkedin for 'test' must be set to a valid LinkedIn URL - '{}' provided".format(invalidLinkedInURL)], cm.output)
            self.assertIsNone(member.linkedin)

    def testSetCrunchbaseValid(self):
        validCrunchbaseURLs = [
            'https://www.crunchbase.com/organization/visual-effects-society'
        ]

        for validCrunchbaseURL in validCrunchbaseURLs:
            member = Member()
            member.crunchbase = validCrunchbaseURL
            self.assertEqual(member.crunchbase,validCrunchbaseURL)

    def testSetCrunchbaseNotValidOnEmpty(self):
        member = Member()
        member.name = 'test'
        member.crunchbase = ''
        self.assertIsNone(member.crunchbase)

    @patch('lfx_landscape_tools.member.Github')
    def test_fetch_repo_404(self, mock_github):
        """Test Path: Organization does not exist (404)."""
        # Setup: Mock the search to raise UnknownObjectException
        mock_instance = mock_github.return_value
        mock_instance.search_repositories.side_effect = UnknownObjectException(404, "Not Found")

        result = Member()._fetch_best_repo_via_api("fake-org")

        self.assertFalse(result)
        mock_instance.search_repositories.assert_called_once()

    @patch('lfx_landscape_tools.member.time.time')
    @patch('lfx_landscape_tools.member.time.sleep')
    @patch('lfx_landscape_tools.member.Github')
    def test_fetch_repo_rate_limit(self, mock_github, mock_sleep, mock_time):
        """Test Path: Rate limit hit, then success."""
        mock_instance = mock_github.return_value
        mock_instance.rate_limiting_resettime = 100
        mock_time.return_value = 90.0

        mock_repo = MagicMock()
        mock_repo.html_url = "https://github.com/org/repo"

        mock_instance.search_repositories.side_effect = [
            RateLimitExceededException(403, "Rate Limit"),
            [mock_repo]
        ]

        result = Member()._fetch_best_repo_via_api("org")

        self.assertEqual(result, "https://github.com/org/repo")
        mock_sleep.assert_called_with(10)
        self.assertEqual(mock_instance.search_repositories.call_count, 2)

    @patch('lfx_landscape_tools.member.Github')
    def test_fetch_repo_retry_on_502(self, mock_github):
        """Test Path: Server error 502 triggers a retry."""
        mock_instance = mock_github.return_value

        # Create a mock exception with status 502
        error_502 = GithubException(502, {"message": "bad gateway"})

        mock_repo = MagicMock()
        mock_repo.html_url = "https://github.com/org/repo"

        # 502 error then success
        mock_instance.search_repositories.side_effect = [error_502, [mock_repo]]

        result = Member()._fetch_best_repo_via_api("org")

        self.assertEqual(result, "https://github.com/org/repo")
        self.assertEqual(mock_instance.search_repositories.call_count, 2)

    @patch('lfx_landscape_tools.member.Github')
    @patch('logging.getLogger')
    def test_fetch_repo_github_exception_generic(self, mock_get_logger, mock_github):
        """Test Path: GithubException with non-502 status (e.g., 403 or 422)."""
        mock_instance = mock_github.return_value

        error_data = {"message": "Resource not accessible by integration"}
        generic_error = GithubException(status=403, data=error_data, headers={})

        mock_instance.search_repositories.side_effect = generic_error

        result = Member()._fetch_best_repo_via_api("org")

        self.assertIsNone(result)
        mock_get_logger.return_value.warning.assert_called_with(error_data)

    @patch('lfx_landscape_tools.member.Github')
    def test_fetch_repo_network_error(self, mock_github):
        """Test Path: Network timeout triggers a retry."""
        mock_instance = mock_github.return_value

        mock_instance.search_repositories.side_effect = [
            socket.timeout("Timeout"),
            [] # Empty list (no repos found)
        ]

        result = Member()._fetch_best_repo_via_api("org")

        self.assertEqual(result, '') # Returns empty string per your logic
        self.assertEqual(mock_instance.search_repositories.call_count, 2)

    def testSetRepoNotValidOnEmpty(self):
        member = Member()
        member.name = 'test'
        member.repo_url = ''
        self.assertIsNone(member.repo_url)

    def testSetRepoGitlab(self):
        member = Member()
        member.name = 'test'
        member.repo_url = 'https://gitlab.com/foo/bar'
        self.assertEqual(member.repo_url,'https://gitlab.com/foo/bar')

    @responses.activate
    def testSetRepoGitHubOrgWithPins(self):
        with unittest.mock.patch('requests_cache.CachedSession', requests.Session):
            member = Member()
            member.name = 'test'
            member.repo_url = 'https://github.com/OpenAssetIO'
            self.assertEqual(member.project_org,'https://github.com/OpenAssetIO')
            self.assertEqual(member.repo_url,'https://github.com/OpenAssetIO/OpenAssetIO')
            attributes = member.toLandscapeItemAttributes()
            self.assertEqual(attributes['extra']['annotations']['project_org'],'https://github.com/OpenAssetIO')
            self.assertEqual(attributes['additional_repos'],[
                {'repo_url': 'https://github.com/OpenAssetIO/OpenAssetIO-MediaCreation'},
                {'repo_url': 'https://github.com/OpenAssetIO/OpenAssetIO-TraitGen'},
                {'repo_url': 'https://github.com/OpenAssetIO/Template-OpenAssetIO-Manager-Python'}
                ])

    @responses.activate
    def testSetRepoGitHubOrgWithoutPins(self):
        with unittest.mock.patch('requests_cache.CachedSession', requests.Session):
            responses.replace(responses.GET,"https://github.com/OpenAssetIO",body="")
            member = Member()
            member.name = 'test'
            member.repo_url = 'https://github.com/OpenAssetIO'
            self.assertEqual(member.project_org,'https://github.com/OpenAssetIO')
            self.assertEqual(member.repo_url,'https://github.com/OpenAssetIO/OpenAssetIO')
            attributes = member.toLandscapeItemAttributes()
            self.assertEqual(attributes['extra']['annotations']['project_org'],'https://github.com/OpenAssetIO')
            self.assertEqual(attributes['additional_repos'],[])

    @patch.object(Member, '_isGitHubOrg', return_value=True)
    @patch.object(Member, '_getPrimaryGitHubRepoFromGitHubOrg')
    def test_repo_url_else_path(self, mock_get_repo, mock_is_org):
        """Tests the 'else' logic (when found_repo_url is None/False)."""
        mock_get_repo.return_value = None

        member = Member()
        member.repo_url = "https://github.com/cncf"

        self.assertIsNone(member.repo_url)
        self.assertIsNone(member.project_org)

    @patch.object(Member, '_isGitHubOrg', return_value=True)
    @patch.object(Member, '_getPrimaryGitHubRepoFromGitHubOrg')
    def test_repo_url_except_path(self, mock_get_repo, mock_is_org):
        """Tests the 'except ValueError' path."""
        mock_get_repo.side_effect = ValueError("API Error")

        with self.assertLogs(level='WARNING') as cm:
            member = Member()
            member.repo_url = "https://github.com/cncf"

            # Verify
            self.assertIn("No public repositories found", cm.output[0])
            self.assertIsNone(member.project_org)

    @patch.object(Member, '_isGitHubOrg', return_value=False)
    def test_get_primary_repo_not_an_org(self, mock_is_org):
        """Test Path 1: Not a GitHub Org (Line 162 fix)."""
        test_url = "https://gitlab.com/something"

        result = Member()._getPrimaryGitHubRepoFromGitHubOrg(test_url)

        self.assertEqual(result, test_url)

    @patch.object(Member, '_isGitHubOrg', return_value=False)
    def test_get_pinned_not_an_org(self, mock_is_org):
        """Test Path 1: Not a GitHub Org. Clears the 174 -> 175 jump."""
        test_url = "https://gitlab.com/cncf"
        result = Member()._getPinnedGithubReposFromGithubOrg(test_url)

        self.assertIsInstance(result, list)
        self.assertEqual(result[0], 'h')

    @patch.object(Member, '_isGitHubOrg', return_value=True)
    @patch('requests_cache.CachedSession.get')
    @patch('logging.getLogger')
    def test_get_pinned_http_error(self, mock_get_logger, mock_get, mock_is_org):
        """Test Path 3: Handle RequestException (Pathological Path)."""
        # Setup: Force raise_for_status to fail
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error")
        mock_get.return_value = mock_response

        # Execute
        result = Member()._getPinnedGithubReposFromGithubOrg("https://github.com/cncf")

        # Verify
        self.assertEqual(result, [])
        mock_get_logger.return_value.error.assert_called()

    def testSetCrunchbaseNotValid(self):
        invalidCrunchbaseURLs = [
            'https://yahoo.com',
            'https://www.crunchbase.com/person/johndoe'
        ]

        for invalidCrunchbaseURL in invalidCrunchbaseURLs:
            member = Member()
            member.name = 'test'
            with self.assertLogs() as cm:
                member.crunchbase = invalidCrunchbaseURL
                self.assertEqual(["WARNING:root:Member.crunchbase for '{name}' must be set to a valid Crunchbase URL - '{crunchbase}' provided".format(crunchbase=invalidCrunchbaseURL,name=member.name)], cm.output)
            self.assertIsNone(member.crunchbase)

    def testNoneCrunchbaseNotInLandscapeItemAttributes(self):
        member = Member()
        member.crunchbase = None
        dict = member.toLandscapeItemAttributes()
        self.assertNotIn('crunchbase',dict)

    def testSethomepage_urlValid(self):
        validhomepage_urlURLs = [
            {'before':'https://crunchbase.com/','after':'https://crunchbase.com/'},
            {'before':'sony.com/en','after':'https://sony.com/en'}
        ]

        for validhomepage_urlURL in validhomepage_urlURLs:
            member = Member()
            member.homepage_url = validhomepage_urlURL['before']
            self.assertEqual(member.homepage_url,validhomepage_urlURL['after'])

    def testSethomepage_urlNotValidOnEmpty(self):
        member = Member()
        member.name = 'test'
        with self.assertLogs() as cm:
            member.homepage_url = ''
            self.assertEqual(["WARNING:root:Member.homepage_url must be not be blank for 'test'"], cm.output)
        self.assertIsNone(member.homepage_url)

    def testSethomepage_urlNotValid(self):
        invalidhomepage_urlURLs = [
            'htps:/yahoo.com',
            '/dog/'
        ]

        for invalidhomepage_urlURL in invalidhomepage_urlURLs:
            member = Member()
            member.name = 'test'
            with self.assertLogs() as cm:
                member.homepage_url = invalidhomepage_urlURL
                self.assertEqual(["WARNING:root:Member.homepage_url for 'test' must be set to a valid homepage_url - '{homepage_url}' provided".format(homepage_url=invalidhomepage_urlURL)], cm.output)

            self.assertIsNone(member.homepage_url)

    def testSetLogoValid(self):
        validLogos = [
            'dog.svg'
        ]

        for validLogo in validLogos:
            with unittest.mock.patch("lfx_landscape_tools.svglogo.open", unittest.mock.mock_open(read_data="data")) as mock_file:
                member = Member()
                member.name = 'dog'
                member.logo = validLogo
                self.assertEqual(member.logo.filename(member.name),validLogo)

    def testSetLogoNotValidOnEmpty(self):
        member = Member()
        member.name = 'test'
        with self.assertLogs() as cm:
            member.logo = ''
            self.assertEqual(["WARNING:root:Member.logo must be not be blank for 'test'"], cm.output)
        self.assertIsNone(member.logo)

    def testSetLogoNotValid(self):
        invalidLogos = [
            'dog.png',
            'dog.svg.png'
        ]

        for invalidLogo in invalidLogos:
            with unittest.mock.patch("lfx_landscape_tools.svglogo.open", unittest.mock.mock_open(read_data="<text")) as mock_file:
                member = Member()
                member.name = 'test'
                with self.assertLogs() as cm:
                    member.logo = invalidLogo
                    self.assertEqual(["WARNING:root:Member.logo for '{name}' invalid format".format(name=member.name)], cm.output)
                self.assertIsNone(member.logo)

    def testTwitterValid(self):
        validTwitters = [
            'dog',
            'https://twitter.com/dog',
            'http://twitter.com/dog',
            'https://www.twitter.com/dog',
            'http://twitter.com/dog'
        ]

        for validTwitter in validTwitters:
            member = Member()
            member.name = 'test'
            member.twitter = validTwitter
            self.assertEqual(member.twitter,'https://twitter.com/dog')

    def testSetTwitterNotValid(self):
        invalidTwitters = [
            'https://notwitter.com/dog',
            'http://facebook.com'
        ]

        for invalidTwitter in invalidTwitters:
            member = Member()
            member.name = 'test'
            with self.assertLogs() as cm:
                member.twitter = invalidTwitter
                self.assertEqual(["WARNING:root:Member.twitter for 'test' must be either a Twitter handle, or the URL to a twitter handle - '{twitter}' provided".format(twitter=invalidTwitter)], cm.output)
            self.assertIsNone(member.twitter)

    def testSetTwitterNull(self):
        member = Member()
        member.name = 'test'
        member.twitter = None
        self.assertIsNone(member.twitter)

    def testSetExtra(self):
        member = Member()
        member.extra = {
                'foo': 'foo',
                'happy': None,
                'annotations': {'bar': 'bar', 'sad': None},
                'accepted': '2025-01-01',
                'other_links': [
                    {'name':'test1','url':'https://google.com'},
                    {'name':'test2','url':' '},
                    {'name':'test3','url':None},
                    {'name':'test4','url':'https://cncf.io'},
                    ]
                }

        self.assertEqual(member.extra['annotations']['foo'],'foo')
        self.assertNotIn('foo',member.extra)
        self.assertNotIn('happy',member.extra)
        self.assertNotIn('happy',member.extra['annotations'])
        self.assertEqual(member.extra['accepted'],'2025-01-01')
        self.assertEqual(member.extra['annotations']['bar'],'bar')
        self.assertNotIn('sad',member.extra['annotations'])
        self.assertEqual(len(member.extra['other_links']),2)
        self.assertIn({'name':'test1','url':'https://google.com'},member.extra['other_links'])
        self.assertNotIn({'name':'test2','url':' '},member.extra['other_links'])
        self.assertNotIn({'name':'test3','url':None},member.extra['other_links'])
        self.assertIn({'name':'test4','url':'https://cncf.io'},member.extra['other_links'])

    def testSetExtraNotDict(self):
        member = Member()
        member.extra = "This won't work"
        self.assertEqual(member.extra,{})

    def testToLandscapeItemAttributes(self):
        member = Member()
        member.name = 'test'
        member.homepage_url = 'https://foo.com'
        member.membership = 'Gold'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        member.extra = {}
        member.foo = 'foo'
        dict = member.toLandscapeItemAttributes()

        self.assertEqual(dict.get('name'),member.name)
        self.assertEqual(dict.get('homepage_url'),member.homepage_url)
        self.assertEqual(dict.get('crunchbase'),member.crunchbase)
        self.assertNotIn('extra',dict)
        self.assertNotIn('membership',dict)
        self.assertIsNone(dict.get('logo'))
        self.assertIsNone(dict.get('item'))
        self.assertIsNone(dict.get('foo'))

    def testToLandscapeItemAttributesProjectOrg(self):
        member = Member()
        member.name = 'test'
        member.homepage_url = 'https://foo.com'
        member.membership = 'Gold'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        member.extra = {}
        member.foo = 'foo'
        member.project_org = 'https://github.com/foobar'
        dict = member.toLandscapeItemAttributes()

        self.assertEqual(dict.get('name'),member.name)
        self.assertEqual(dict.get('homepage_url'),member.homepage_url)
        self.assertEqual(dict.get('crunchbase'),member.crunchbase)
        self.assertNotIn('membership',dict)
        self.assertIsNone(dict.get('logo'))
        self.assertIsNone(dict.get('item'))
        self.assertIsNone(dict.get('foo'))
        self.assertEqual(dict.get('extra',{}).get('annotations',{}).get('project_org'),member.project_org)

    def testToLandscapeItemAttributesEmptyCrunchbase(self):
        member = Member()
        member.name = 'test'
        member.homepage_url = 'https://foo.com'
        member.membership = 'Gold'
        member.linkedin = 'https://www.linkedin.com/company/208777'
        member.project_org = 'https://github.com/OpenAssetIO'
        member.extra = {'foo': 'foo', 'accepted': "2023-05-14", 'annotations': {'foo':'foo'}, 'other_links': [{'name':'foo','url':'https://google.com'}]}
        member.second_path = ['list2','list3']
        dict = member.toLandscapeItemAttributes()

        self.assertEqual(dict.get('name'),member.name)
        self.assertEqual(dict.get('homepage_url'),member.homepage_url)
        self.assertEqual(dict.get('organization',{}).get('name'),member.name)
        self.assertEqual(dict.get('organization',{}).get('linkedin'),member.linkedin)
        self.assertIsNone(dict.get('logo'))
        self.assertIsNone(dict.get('item'))
        self.assertNotIn('crunchbase',dict)
        self.assertEqual(dict.get('extra',{}).get('linkedin_url'),member.linkedin)
        self.assertEqual(dict.get('extra',{}).get('accepted'),"2023-05-14")
        self.assertEqual(dict.get('extra',{}).get('annotations',{}).get('foo'),'foo')
        self.assertEqual(dict.get('extra',{}).get('annotations',{}).get('project_org'),'https://github.com/OpenAssetIO')
        self.assertIsNone(dict.get('extra',{}).get('foo'))
        self.assertIn('list2',member.second_path)
        self.assertIn('list3',member.second_path)

    def testToLandscapeItemAttributesWithSuffix(self):
        member = Member()
        member.entrysuffix = ' (testme)'
        member.name = 'test'
        member.homepage_url = 'https://foo.com'
        member.membership = 'Gold'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        member.linkedin = 'https://www.linkedin.com/company/208777'
        dict = member.toLandscapeItemAttributes()

        self.assertEqual(dict.get('name'),member.name+" (testme)")
        self.assertEqual(dict.get('homepage_url'),member.homepage_url)
        self.assertEqual(dict.get('crunchbase'),member.crunchbase)
        self.assertEqual(dict.get('extra',{}).get('linkedin_url'),member.linkedin)
        self.assertIsNone(dict.get('logo'))
        self.assertIsNone(dict.get('item'))
        self.assertNotIn('membership',dict)

    def testIsValidLandscapeItem(self):
        member = Member()
        member.name = 'test'
        member.homepage_url = 'https://foo.com'
        with unittest.mock.patch("lfx_landscape_tools.svglogo.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            member.logo = 'Gold.svg'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        self.assertTrue(member.isValidLandscapeItem())

    def testIsValidLandscapeItemEmptyCrunchbase(self):
        member = Member()
        member.name = 'test3'
        member.homepage_url = 'https://foo.com'
        with unittest.mock.patch("lfx_landscape_tools.svglogo.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            member.logo = 'Gold.svg'

        self.assertTrue(member.isValidLandscapeItem())

    def testIsValidLandscapeItemEmptyname(self):
        member = Member()
        member.name = ''
        member.homepage_url = 'https://foo.com'
        with unittest.mock.patch("lfx_landscape_tools.svglogo.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            member.logo = 'Gold.svg'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        self.assertFalse(member.isValidLandscapeItem())
        self.assertIn('name',member.invalidLandscapeItemAttributes())

    def testIsValidLandscapeItemEmptyhomepage_urlLogo(self):
        member = Member()
        member.name = 'foo'
        member.homepage_url = ''
        with unittest.mock.patch("lfx_landscape_tools.svglogo.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            member.logo = ''
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        self.assertFalse(member.isValidLandscapeItem())
        self.assertIn('logo',member.invalidLandscapeItemAttributes())
        self.assertIn('homepage_url',member.invalidLandscapeItemAttributes())

    def testOverlay(self):
        membertooverlay = Member()
        membertooverlay.name = 'test2'
        membertooverlay.homepage_url = 'https://foo.com'
        with unittest.mock.patch("lfx_landscape_tools.svglogo.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            membertooverlay.logo = 'gold.svg'
        membertooverlay.membership = 'Gold'
        membertooverlay.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society-bad'
        membertooverlay.organization = {'name':'foo'}
        membertooverlay.extra = {'foo': 'foo', 'accepted': "2023-05-14", 'annotations': {'foo':'foo'}, 'other_links': [{'name':'link1','url':'https://link1.com'}]}
        membertooverlay.second_path = ['list1','list3']

        member = Member()
        member.name = 'test'
        member.homepage_url = 'https://foo.org'
        member.membership = 'Silver'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        member.twitter = 'https://twitter.com/mytwitter'
        member.stock_ticker = None
        member.extra = {'accepted': "2024-05-14", 'annotations': {'bar': 'bar'}, 'other_links': [{'name':'link2','url':'https://link2.com'}]}
        member.second_path = ['list2','list3']

        with unittest.mock.patch("lfx_landscape_tools.svglogo.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            member.overlay(membertooverlay)

        self.assertEqual(member.name,'test2')
        self.assertEqual(member.homepage_url,'https://foo.com/')
        self.assertEqual(member.logo.filename(member.name),'gold.svg')
        self.assertEqual(member.membership,'Gold')
        self.assertEqual(member.crunchbase, 'https://www.crunchbase.com/organization/visual-effects-society-bad')
        self.assertEqual(member.twitter,'https://twitter.com/mytwitter')
        self.assertIsNone(member.stock_ticker)
        self.assertEqual(member.organization,{})
        self.assertEqual(member.extra['accepted'],"2023-05-14")
        self.assertEqual(member.extra['annotations']['bar'],'bar')
        self.assertEqual(member.extra['annotations']['foo'],'foo')
        self.assertIsNone(member.extra.get('foo'))
        self.assertIn('list1',member.second_path)
        self.assertIn('list2',member.second_path)
        self.assertIn('list3',member.second_path)

    def testOverlayLogo(self):
        membertooverlay = Member()
        membertooverlay.name = 'test'
        membertooverlay.homepage_url = 'https://foo.com'
        membertooverlay.logo = SVGLogo(contents='<svg>gold.svg</svg>')

        member = Member()
        member.name = 'test'
        member.homepage_url = 'https://foo.com'
        member.logo = SVGLogo(contents='<svg>silver.svg</svg>')

        member.overlay(membertooverlay)

        self.assertEqual(member.name,'test')
        self.assertEqual(member.homepage_url,'https://foo.com/')
        self.assertEqual(str(member.logo),'<svg>gold.svg</svg>')

    def testOverlayOtherLinks(self):
        membertooverlay = Member()
        membertooverlay.name = 'test'
        membertooverlay.homepage_url = 'https://foo.com'
        membertooverlay.extra = {
                'other_links': [
                    {'name':'test1','url':'https://google.com'},
                    {'name':'test2','url':' '},
                    {'name':'test3','url':None},
                    {'name':'test4','url':'https://cncf.io'},
                    ]
                }

        member = Member()
        member.name = 'test'
        member.homepage_url = 'https://foo.com'
        member.extra = {
                'other_links': [
                    {'name':'test1','url':'https://google.com'},
                    {'name':'test2','url':' '},
                    {'name':'test3','url':None},
                    {'name':'test5','url':'https://aswf.io'},
                    ]
                }
        member.overlay(membertooverlay)

        self.assertEqual(member.name,'test')
        self.assertEqual(member.homepage_url,'https://foo.com/')
        self.assertEqual(len(member.extra['other_links']),3)
        self.assertIn({'name':'test1','url':'https://google.com'},member.extra['other_links'])
        self.assertNotIn({'name':'test2','url':' '},member.extra['other_links'])
        self.assertNotIn({'name':'test3','url':None},member.extra['other_links'])
        self.assertIn({'name':'test4','url':'https://cncf.io'},member.extra['other_links'])
        self.assertIn({'name':'test5','url':'https://aswf.io'},member.extra['other_links'])

    def testOverlayOnlyKeys(self):
        membertooverlay = Member()
        membertooverlay.name = 'test'
        membertooverlay.homepage_url = 'https://foo.com'
        with unittest.mock.patch("lfx_landscape_tools.svglogo.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            membertooverlay.logo = 'gold.svg'
        membertooverlay.membership = 'Gold'
        membertooverlay.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society-bad'
        membertooverlay.organization = {'name':'foo'}

        member = Member()
        member.name = 'test'
        member.homepage_url = 'https://foo.org'
        with unittest.mock.patch("lfx_landscape_tools.svglogo.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            member.logo = 'silver.svg'
        member.membership = 'Silver'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        member.twitter = 'https://twitter.com/mytwitter'
        member.stock_ticker = None

        with unittest.mock.patch("lfx_landscape_tools.svglogo.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            membertooverlay.overlay(member,['homepage_url'])

        self.assertEqual(member.name,'test')
        self.assertEqual(member.homepage_url,'https://foo.org/')
        self.assertEqual(member.logo.filename(member.name),'silver.svg')
        self.assertEqual(member.membership,'Silver')
        self.assertEqual(member.crunchbase, 'https://www.crunchbase.com/organization/visual-effects-society')
        self.assertEqual(member.twitter,'https://twitter.com/mytwitter')
        self.assertIsNone(member.stock_ticker)
        self.assertEqual(member.organization,{})

    def testOverlayItemThrowsException(self):
        membertooverlay = Member()
        membertooverlay.name = 'test2'
        membertooverlay.homepage_url = 'https://foo.com'
        with unittest.mock.patch("lfx_landscape_tools.svglogo.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            membertooverlay.logo = 'gold.svg'
        membertooverlay.membership = 'Gold'

        membertooverlay.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society-bad'
        membertooverlay.organization = {'name':'foo'}

        member = Member()
        member.name = 'test'
        member.homepage_url = 'https://foo.org'
        member.membership = 'Silver'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        member.twitter = 'https://twitter.com/mytwitter'
        member.stock_ticker = None

        with unittest.mock.patch("lfx_landscape_tools.svglogo.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            membertooverlay.overlay(member)

    @responses.activate
    def testHostLogo(self):
        with tempfile.TemporaryDirectory() as tempdir:
            tmpfilename = tempfile.NamedTemporaryFile(dir=tempdir,mode='w',delete=False,suffix='.svg')
            tmpfilename.write('this is a file')
            tmpfilename.close()

            member = Member()
            member.name = 'dog'
            member.logo = SVGLogo(name='dog')
            member.hostLogo(tempdir)
            self.assertTrue(os.path.exists(os.path.join(tempdir,'dog.svg')))

    def testExtra(self):
        member = Member()
        member.extra = {
            "facebook_url": "https://facebook.com",
            "reddit_url": None,
            "youtube_url": "nil",
        }

        self.assertEqual(member.extra.get("facebook_url"),"https://facebook.com")
        self.assertIsNone(member.extra.get("reddit_url"))
        self.assertIsNone(member.extra.get("youtube_url"))

    @patch('requests_cache.CachedSession.get')
    @patch('logging.getLogger')
    def test_init_request_exception(self, mock_get_logger, mock_get):
        """Test Path 1: GitHub is down or URL is 404."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection Timeout")

        Member()

        mock_get_logger.return_value.error.assert_called()
        args = mock_get_logger.return_value.error.call_args[0][0]
        self.assertIn("Cannot load data file schema", args)
        self.assertIn("Connection Timeout", args)

    @patch('requests_cache.CachedSession.get')
    @patch('ruamel.yaml.YAML.load')
    @patch('logging.getLogger')
    def test_init_yaml_exception(self, mock_get_logger, mock_yaml_load, mock_get):
        """Test Path 2: File loads but the YAML is malformed."""
        mock_response = MagicMock()
        mock_response.text = "invalid: yaml: : :"
        mock_get.return_value = mock_response

        mock_yaml_load.side_effect = ruamel.yaml.YAMLError("Scanner Error")

        Member()

        mock_get_logger.return_value.error.assert_called()
        args = mock_get_logger.return_value.error.call_args[0][0]
        self.assertIn("is not valid YAML", args)
        self.assertIn("Scanner Error", args)

    @patch('requests_cache.CachedSession.get')
    def test_init_success_path(self, mock_get):
        """Test Path 3: The 'else' block (Success)."""
        # Setup: Mock a valid response structure
        mock_response = MagicMock()
        mock_response.text = "valid yaml"
        mock_get.return_value = mock_response

        # Mock the nested dict structure expected in the 'else' block
        valid_schema = {
            'categories': [{
                'subcategories': [{
                    'items': [{'key': 'value'}]
                }]
            }]
        }

        with patch('ruamel.yaml.YAML.load', return_value=valid_schema):
            m = Member()
            self.assertEqual(m.itemschema, {'key': 'value'})

    def test_sanitize_links_not_a_list(self):
        """Test Path 1: Input is not a list (Clears 294 -> 295)."""
        self.assertEqual(Member()._sanitize_links(None), [])
        self.assertEqual(Member()._sanitize_links("not a list"), [])
        self.assertEqual(Member()._sanitize_links({"name": "test"}), [])

    def test_get_nested_attr_invalid_base(self):
        """Test Path 1: Base attribute is missing or not a dict (Clears 341 -> 342)."""
        self.assertIsNone(Member()._get_nested_attr('non_existent_key'))

    def test_get_nested_attr_triple_depth(self):
        member = Member()
        # Mock schema so 'level1' is recognized as a valid extra field, not an annotation
        member.itemschema = {'extra': ['level1']}

        # Set the data
        member.extra = {'level1': {'level2': 'target_value'}}

        # Trigger the 3rd level depth check (subsubkey)
        # This will now find self.extra['level1']['level2']
        result = member._get_nested_attr('extra', 'level1', 'level2')
        self.assertEqual(result, 'target_value')

    def test_build_nested_attributes_complex_schema(self):
        member = Member()
        member.name = "Test"

        # 1. Provide a valid Crunchbase to keep the mapper from overwriting 'organization'
        member.crunchbase = "https://www.crunchbase.com/organization/test"

        # 2. Define the 3-level schema
        member.itemschema = {
            'organization': {
                'custom': {
                    'sub_custom': None
                }
            }
        }

        # 3. Populate the data
        member.organization = {
            'custom': {
                'sub_custom': 'found_it'
            }
        }

        # 4. Process
        result = member.toLandscapeItemAttributes()

        # 5. Assertions
        # Now result['organization'] should contain the mapped nested data
        self.assertIn('organization', result)
        self.assertIn('custom', result['organization'])
        self.assertEqual(result['organization']['custom']['sub_custom'], 'found_it')

    @patch('requests_cache.CachedSession.get')
    def test_final_branch_coverage_379(self, mock_get):
        # 1. Mock the initial schema fetch so Member() doesn't crash or hit the web
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        # This minimal YAML satisfies the [0] indexing in Member.__init__
        mock_resp.text = "categories: [{subcategories: [{items: [{}]}]}]"
        mock_get.return_value = mock_resp

        member = Member()
        member.name = "TestProject"

        # CRITICAL: Set a crunchbase so the 'if not self.crunchbase'
        # block doesn't overwrite your organization dict later.
        member.crunchbase = "https://www.crunchbase.com/organization/test"

        # 2. Setup the itemschema to force the loop cycle.
        # The key 'organization' triggers _build_nested_attributes.
        # Inside that, we need TWO keys.
        # The FIRST must be a dict (to hit 379).
        # The SECOND must exist to force the loop back to the top (369).
        member.itemschema = {
            'organization': {
                'nested_dict': {'deep_key': None}, # Hits line 379
                'second_item': None                # Forces jump 379 -> 369
            }
        }

        # 3. Provide the data that matches the schema
        member.organization = {
            'nested_dict': {'deep_key': 'value_1'},
            'second_item': 'value_2'
        }

        # 4. Run the method
        result = member.toLandscapeItemAttributes()

        # 5. Verify the results to ensure the loop actually processed both
        self.assertIn('organization', result)
        self.assertEqual(result['organization']['nested_dict']['deep_key'], 'value_1')
        self.assertEqual(result['organization']['second_item'], 'value_2')

    def test_build_nested_attributes_or_none(self):
        """Clears the 'or None' branch on line 383."""
        member = Member()
        # Call with a schema but no matching data in the member object
        # result will be {} so it returns None
        res = member._build_nested_attributes('organization', {'missing': {'key': None}})
        self.assertIsNone(res)

    def test_build_nested_attributes_full_loop_cycle(self):
        """Clears 379 -> 369 by forcing the loop to continue after a sub_result match."""
        member = Member()
        member.name = "Test Member"
        member.crunchbase = "https://www.crunchbase.com/organization/test"

        # We need a schema with multiple items where the FIRST item
        # triggers the sub_result logic to prove the loop continues.
        member.itemschema = {
            'organization': {
                'deep_item': {      # Item 1: Triggers line 379
                    'field_a': None
                },
                'shallow_item': None, # Item 2: Forces loop jump from 379 back to 369
                'empty_item': None    # Item 3: Ensures loop can handle a skip
            }
        }

        # Data for the member
        member.organization = {
            'deep_item': {
                'field_a': 'value_a'
            },
            'shallow_item': 'value_b'
            # 'empty_item' is missing to exercise the 'if not val: continue' on line 371
        }

        # Trigger the mapper
        result = member.toLandscapeItemAttributes()

        # Assertions to ensure all paths were exercised
        org_res = result['organization']
        self.assertEqual(org_res['deep_item']['field_a'], 'value_a')
        self.assertEqual(org_res['shallow_item'], 'value_b')
        self.assertNotIn('empty_item', org_res)

    def test_build_nested_attributes_completion_loop(self):
        """
        Clears 379 -> 369 specifically.
        Forces the interpreter to return to the loop header after line 379.
        """
        member = Member()
        member.name = "CoverageTest"

        # We use a dummy attribute to avoid all property logic
        member.test_data = {
            'first_nested': {'inner_key': 'value_1'}, # Item 1: Hits line 379
            'second_item': 'value_2'                  # Item 2: Forces loop jump
        }

        # The schema MUST have two items, and the nested one MUST be first.
        # We use collections.OrderedDict if you're on an old Python,
        # but standard dicts work in 3.7+
        test_schema = {
            'first_nested': {'inner_key': None},
            'second_item': None
        }

        # Execute the helper directly
        result = member._build_nested_attributes('test_data', test_schema)

        # If both items are in the result, the loop MUST have returned to 369
        # after processing 'first_nested' at line 379.
        self.assertEqual(result['first_nested']['inner_key'], 'value_1')
        self.assertEqual(result['second_item'], 'value_2')
