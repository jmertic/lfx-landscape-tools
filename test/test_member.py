#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

import unittest
import tempfile
import os
import responses
import requests
import requests_cache
import logging

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
            with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
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
            with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="<text")) as mock_file:
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

    def testToLandscapeItemAttributesEmptyCrunchbase(self):
        member = Member()
        member.name = 'test'
        member.homepage_url = 'https://foo.com'
        member.membership = 'Gold'
        member.linkedin = 'https://www.linkedin.com/company/208777'
        member.project_org = 'https://github.com/OpenAssetIO'
        member.extra = {'foo': 'foo', 'accepted': "2023-05-14", 'annotations': {'foo':'foo'}}
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
        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            member.logo = 'Gold.svg'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        self.assertTrue(member.isValidLandscapeItem())

    def testIsValidLandscapeItemEmptyCrunchbase(self):
        member = Member()
        member.name = 'test3'
        member.homepage_url = 'https://foo.com'
        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            member.logo = 'Gold.svg'

        self.assertTrue(member.isValidLandscapeItem())
    
    def testIsValidLandscapeItemEmptyname(self):
        member = Member()
        member.name = ''
        member.homepage_url = 'https://foo.com'
        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            member.logo = 'Gold.svg'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        self.assertFalse(member.isValidLandscapeItem())
        self.assertIn('name',member.invalidLandscapeItemAttributes())
    
    def testIsValidLandscapeItemEmptyhomepage_urlLogo(self):
        member = Member()
        member.name = 'foo'
        member.homepage_url = ''
        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            member.logo = ''
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        self.assertFalse(member.isValidLandscapeItem())
        self.assertIn('logo',member.invalidLandscapeItemAttributes())
        self.assertIn('homepage_url',member.invalidLandscapeItemAttributes())

    def testOverlay(self):
        membertooverlay = Member()
        membertooverlay.name = 'test2'
        membertooverlay.homepage_url = 'https://foo.com'
        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            membertooverlay.logo = 'gold.svg'
        membertooverlay.membership = 'Gold'
        membertooverlay.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society-bad'
        membertooverlay.organization = {'name':'foo'}
        membertooverlay.extra = {'foo': 'foo', 'accepted': "2023-05-14", 'annotations': {'foo':'foo'}}
        membertooverlay.second_path = ['list1','list3']

        member = Member()
        member.name = 'test'
        member.homepage_url = 'https://foo.org'
        member.membership = 'Silver'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        member.twitter = 'https://twitter.com/mytwitter'
        member.stock_ticker = None
        member.extra = {'accepted': "2024-05-14", 'annotations': {'bar': 'bar'}}
        member.second_path = ['list2','list3']

        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
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
        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            membertooverlay.logo = 'gold.svg'
        membertooverlay.membership = 'Gold'
        membertooverlay.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society-bad'
        membertooverlay.organization = {'name':'foo'} 

        member = Member()
        member.name = 'test'
        member.homepage_url = 'https://foo.org'
        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            member.logo = 'silver.svg'
        member.membership = 'Silver'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        member.twitter = 'https://twitter.com/mytwitter'
        member.stock_ticker = None

        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
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
        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
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

        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
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

if __name__ == '__main__':
    unittest.main()
