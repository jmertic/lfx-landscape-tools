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
        member.orgname = 'test'
        member.linkedin = ''
        self.assertIsNone(member.linkedin)

    def testSetLinkedNotValid(self):
        invalidLinkedInURLs = [
            'https://yahoo.com',
            'https://www.crunchbase.com/person/johndoe'
        ]

        for invalidLinkedInURL in invalidLinkedInURLs:
            member = Member()
            member.orgname = 'test'
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
        member.orgname = 'test'
        member.crunchbase = ''
        self.assertIsNone(member.crunchbase)

    def testSetRepoNotValidOnEmpty(self):
        member = Member()
        member.orgname = 'test'
        member.repo_url = ''
        self.assertIsNone(member.repo_url)
    
    def testSetRepoGitlab(self):
        member = Member()
        member.orgname = 'test'
        member.repo_url = 'https://gitlab.com/foo/bar'
        self.assertEqual(member.repo_url,'https://gitlab.com/foo/bar')

    def testSetCrunchbaseNotValid(self):
        invalidCrunchbaseURLs = [
            'https://yahoo.com',
            'https://www.crunchbase.com/person/johndoe'
        ]

        for invalidCrunchbaseURL in invalidCrunchbaseURLs:
            member = Member()
            member.orgname = 'test'
            with self.assertLogs() as cm:
                member.crunchbase = invalidCrunchbaseURL
                self.assertEqual(["WARNING:root:Member.crunchbase for '{orgname}' must be set to a valid Crunchbase URL - '{crunchbase}' provided".format(crunchbase=invalidCrunchbaseURL,orgname=member.orgname)], cm.output)
            self.assertIsNone(member.crunchbase)

    def testSetWebsiteValid(self):
        validWebsiteURLs = [
            {'before':'https://crunchbase.com/','after':'https://crunchbase.com/'},
            {'before':'sony.com/en','after':'https://sony.com/en'}
        ]

        for validWebsiteURL in validWebsiteURLs:
            member = Member()
            member.website = validWebsiteURL['before']
            self.assertEqual(member.website,validWebsiteURL['after'])

    def testSetWebsiteNotValidOnEmpty(self):
        member = Member()
        member.orgname = 'test'
        with self.assertLogs() as cm:
            member.website = ''
            self.assertEqual(["WARNING:root:Member.website must be not be blank for 'test'"], cm.output)
        self.assertIsNone(member.website)

    def testSetWebsiteNotValid(self):
        invalidWebsiteURLs = [
            'htps:/yahoo.com',
            '/dog/'
        ]

        for invalidWebsiteURL in invalidWebsiteURLs:
            member = Member()
            member.orgname = 'test'
            with self.assertLogs() as cm:
                member.website = invalidWebsiteURL
                self.assertEqual(["WARNING:root:Member.website for 'test' must be set to a valid website - '{website}' provided".format(website=invalidWebsiteURL)], cm.output)

            self.assertIsNone(member.website)

    def testSetLogoValid(self):
        validLogos = [
            'dog.svg'
        ]

        for validLogo in validLogos:
            with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
                member = Member()
                member.orgname = 'dog'
                member.logo = validLogo
                self.assertEqual(member.logo,validLogo)

    def testSetLogoNotValidOnEmpty(self):
        member = Member()
        member.orgname = 'test'
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
                member.orgname = 'test'
                with self.assertLogs() as cm:
                    member.logo = invalidLogo
                    self.assertEqual(["WARNING:root:Member.logo for '{orgname}' invalid format".format(orgname=member.orgname)], cm.output)
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
            member.orgname = 'test'
            member.twitter = validTwitter
            self.assertEqual(member.twitter,'https://twitter.com/dog')

    def testSetTwitterNotValid(self):
        invalidTwitters = [
            'https://notwitter.com/dog',
            'http://facebook.com'
        ]

        for invalidTwitter in invalidTwitters:
            member = Member()
            member.orgname = 'test'
            with self.assertLogs() as cm:
                member.twitter = invalidTwitter
                self.assertEqual(["WARNING:root:Member.twitter for 'test' must be either a Twitter handle, or the URL to a twitter handle - '{twitter}' provided".format(twitter=invalidTwitter)], cm.output)
            self.assertIsNone(member.twitter)

    def testSetTwitterNull(self):
        member = Member()
        member.orgname = 'test'
        member.twitter = None
        self.assertIsNone(member.twitter)

    def testToLandscapeItemAttributes(self):
        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.com'
        member.membership = 'Gold'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        member.extra = []
        dict = member.toLandscapeItemAttributes()

        self.assertEqual(dict.get('name'),member.orgname)
        self.assertEqual(dict.get('homepage_url'),member.website)
        self.assertEqual(dict.get('crunchbase'),member.crunchbase)
        self.assertNotIn('extra',dict)
        self.assertNotIn('membership',dict)
        self.assertIsNone(dict.get('logo'))
        self.assertIsNone(dict.get('item'))

    def testToLandscapeItemAttributesEmptyCrunchbase(self):
        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.com'
        member.membership = 'Gold'
        dict = member.toLandscapeItemAttributes()

        self.assertEqual(dict.get('name'),member.orgname)
        self.assertEqual(dict.get('homepage_url'),member.website)
        self.assertEqual(dict.get('organization',{}).get('name'),member.orgname)
        self.assertIsNone(dict.get('logo'))
        self.assertIsNone(dict.get('item'))
        self.assertNotIn('crunchbase',dict)
    
    def testToLandscapeItemAttributesWithSuffix(self):
        member = Member()
        member.entrysuffix = ' (testme)'
        member.orgname = 'test'
        member.website = 'https://foo.com'
        member.membership = 'Gold'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        dict = member.toLandscapeItemAttributes()

        self.assertEqual(dict.get('name'),member.orgname+" (testme)")
        self.assertEqual(dict.get('homepage_url'),member.website)
        self.assertEqual(dict.get('crunchbase'),member.crunchbase)
        self.assertIsNone(dict.get('logo'))
        self.assertIsNone(dict.get('item'))
        self.assertNotIn('membership',dict)

    def testIsValidLandscapeItem(self):
        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.com'
        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            member.logo = 'Gold.svg'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        self.assertTrue(member.isValidLandscapeItem())

    def testIsValidLandscapeItemEmptyCrunchbase(self):
        member = Member()
        member.orgname = 'test3'
        member.website = 'https://foo.com'
        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            member.logo = 'Gold.svg'

        self.assertTrue(member.isValidLandscapeItem())
    
    def testIsValidLandscapeItemEmptyOrgname(self):
        member = Member()
        member.orgname = ''
        member.website = 'https://foo.com'
        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            member.logo = 'Gold.svg'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        self.assertFalse(member.isValidLandscapeItem())
        self.assertIn('orgname',member.invalidLandscapeItemAttributes())
    
    def testIsValidLandscapeItemEmptyWebsiteLogo(self):
        member = Member()
        member.orgname = 'foo'
        member.website = ''
        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            member.logo = ''
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        self.assertFalse(member.isValidLandscapeItem())
        self.assertIn('logo',member.invalidLandscapeItemAttributes())
        self.assertIn('website',member.invalidLandscapeItemAttributes())

    def testOverlay(self):
        membertooverlay = Member()
        membertooverlay.name = 'test2'
        membertooverlay.website = 'https://foo.com'
        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            membertooverlay.logo = 'gold.svg'
        membertooverlay.membership = 'Gold'
        membertooverlay.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society-bad'
        membertooverlay.organization = {'name':'foo'} 

        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.org'
        member.membership = 'Silver'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        member.twitter = 'https://twitter.com/mytwitter'
        member.stock_ticker = None

        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            membertooverlay.overlay(member)

        self.assertEqual(member.orgname,'test')
        self.assertEqual(member.website,'https://foo.org/')
        self.assertEqual(member.logo,'gold.svg')
        self.assertEqual(member.membership,'Silver')
        self.assertEqual(member.crunchbase, 'https://www.crunchbase.com/organization/visual-effects-society')
        self.assertEqual(member.twitter,'https://twitter.com/mytwitter')
        self.assertIsNone(member.stock_ticker)
        self.assertEqual(member.organization,{})

    def testOverlayOnlyKeys(self):
        membertooverlay = Member()
        membertooverlay.orgname = 'test'
        membertooverlay.homepage_url = 'https://foo.com'
        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            membertooverlay.logo = 'gold.svg'
        membertooverlay.membership = 'Gold'
        membertooverlay.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society-bad'
        membertooverlay.organization = {'name':'foo'} 

        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.org'
        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            member.logo = 'silver.svg'
        member.membership = 'Silver'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        member.twitter = 'https://twitter.com/mytwitter'
        member.stock_ticker = None

        membertooverlay.overlay(member,['website'])

        self.assertEqual(member.orgname,'test')
        self.assertEqual(member.website,'https://foo.org/')
        self.assertEqual(member.logo,'silver.svg')
        self.assertEqual(member.membership,'Silver')
        self.assertEqual(member.crunchbase, 'https://www.crunchbase.com/organization/visual-effects-society')
        self.assertEqual(member.twitter,'https://twitter.com/mytwitter')
        self.assertIsNone(member.stock_ticker)
        self.assertEqual(member.organization,{})

    def testOverlayItemThrowsException(self):
        membertooverlay = Member()
        membertooverlay.name = 'test2'
        membertooverlay.website = 'https://foo.com'
        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            membertooverlay.logo = 'gold.svg'
        membertooverlay.membership = 'Gold'
        
        membertooverlay.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society-bad'
        membertooverlay.organization = {'name':'foo'} 

        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.org'
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
            member.orgname = 'dog'
            member.logo = SVGLogo(name='dog')
            member.hostLogo(tempdir)
            self.assertTrue(os.path.exists(os.path.join(tempdir,'dog.svg')))

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("debug.log"),
        ]
    )
    
    unittest.main()
