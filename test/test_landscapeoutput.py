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

class TestLandscapeOutput(unittest.TestCase):

    def testNewLandscape(self):
        config = Config()
        config.landscapeMembersCategory = 'test me'
        config.landscapeMembersSubcategories = [
            {"name": "Good Membership", "category": "Good"},
            {"name": "Bad Membership", "category": "Bad"}
            ]
        tmpfilename = tempfile.NamedTemporaryFile(mode='w',delete=False)
        config.landscapefile = os.path.basename(tmpfilename.name)
        config.basedir = os.path.dirname(tmpfilename.name)
        tmpfilename.close()

        landscape = LandscapeOutput(config=config, newLandscape=True)

        self.assertEqual(landscape.landscape['landscape'][0]['name'],'test me')
        self.assertEqual(landscape.landscape['landscape'][0]['subcategories'][0]['name'],"Good")
        self.assertEqual(landscape.landscape['landscape'][0]['subcategories'][1]['name'],"Bad")

        landscape.save()

        with open(tmpfilename.name) as fp:
            self.assertEqual(fp.read(),"""landscape:
  - category:
    name: test me
    subcategories:
      - subcategory:
        name: Good
        items: []
      - subcategory:
        name: Bad
        items: []
""")

    def testNewLandscapeCategory(self):
        testlandscape = """
landscape:
- category:
  name: no test me
  subcategories:
  - subcategory:
    name: Good
    items:
    - item:
      crunchbase: https://www.crunchbase.com/organization/here-technologies
      homepage_url: https://here.com/
      logo: https://raw.githubusercontent.com/ucfoundation/ucf-landscape/master/hosted_logos/here.svg
      name: HERE Global B.V.
      twitter: https://twitter.com/here
"""
        with tempfile.NamedTemporaryFile(mode='w') as tmpfilename:
            tmpfilename.write(testlandscape)
            tmpfilename.flush()

            config = Config()
            config.landscapeMembersCategory = 'test me'
            config.landscapeMembersSubcategories = [
                {"name": "Good Membership", "category": "Good"},
                {"name": "Bad Membership", "category": "Bad"}
                ]
            config.landscapefile = tmpfilename.name

            landscape = LandscapeOutput(config=config)

            self.assertEqual(landscape.landscape['landscape'][0]['name'],'no test me')
            self.assertEqual(landscape.landscape['landscape'][0]['subcategories'][0]['name'],"Good")
            self.assertEqual(landscape.landscape['landscape'][0]['subcategories'][0]['items'][0]['name'],"HERE Global B.V.")
            self.assertEqual(landscape.landscapeItems[0]['name'],"Good")

        landscape.save()

        with open(tmpfilename.name) as fp:
            self.maxDiff = None
            self.assertEqual(fp.read(),"""landscape:
  - category:
    name: no test me
    subcategories:
      - subcategory:
        name: Good
        items:
          - item:
            crunchbase: https://www.crunchbase.com/organization/here-technologies
            homepage_url: https://here.com/
            logo: https://raw.githubusercontent.com/ucfoundation/ucf-landscape/master/hosted_logos/here.svg
            name: HERE Global B.V.
            twitter: https://twitter.com/here
  - category:
    name: test me
    subcategories:
      - subcategory:
        name: Good
        items: []
      - subcategory:
        name: Bad
        items: []
""")
    
    def testLoadLandscape(self):
        testlandscape = """
landscape:
- category:
  name: test me
  subcategories:
  - subcategory:
    name: Good
    items:
    - item:
      crunchbase: https://www.crunchbase.com/organization/here-technologies
      homepage_url: https://here.com/
      logo: https://raw.githubusercontent.com/ucfoundation/ucf-landscape/master/hosted_logos/here.svg
      name: HERE Global B.V.
      twitter: https://twitter.com/here
"""
        with tempfile.NamedTemporaryFile(mode='w') as tmpfilename:
            tmpfilename.write(testlandscape)
            tmpfilename.flush()

            config = Config()
            config.landscapeMembersCategory = 'test me'
            config.landscapeMembersSubcategories = [
                {"name": "Good Membership", "category": "Good"},
                {"name": "Bad Membership", "category": "Bad"}
                ]
            config.landscapefile = tmpfilename.name

            landscape = LandscapeOutput(config=config)

            self.assertEqual(landscape.landscape['landscape'][0]['name'],'test me')
            self.assertEqual(landscape.landscape['landscape'][0]['subcategories'][0]['name'],"Good")
            self.assertEqual(landscape.landscape['landscape'][0]['subcategories'][0]['items'][0]['name'],"HERE Global B.V.")
            self.assertEqual(landscape.landscapeItems[0]['name'],"Good")
    
    def testAddItemToLandscape(self):
        members = LFXMembers(loadData=False,config=Config())
        
        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.com'
        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            member.logo = 'Gold.svg'
        member.membership = 'Premier Membership'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        member.repo_url = "https://github.com/foo/bar"
        members.members.append(member)
        
        member = Member()
        member.orgname = 'test2'
        member.website = 'https://foo.com'
        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            member.logo = 'Gold.svg'
        member.membership = 'Premiere Membership'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        member.repo_url = "https://github.com/foo/bar"
        members.members.append(member)

        member = Member()
        member.orgname = 'test3'
        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            member.logo = 'Gold.svg'
        member.membership = 'Premier Membership'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        member.repo_url = "https://github.com/foo/bar"
        members.members.append(member)
        
        landscape = LandscapeOutput(config=Config(),newLandscape=True)
        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            landscape.addItems(members)

        self.assertEqual(landscape.landscapeItems[0]['name'],'Premier')
        self.assertEqual(landscape.landscapeItems[0]['items'][0]['name'],"test")
        self.assertEqual(landscape.landscapeItems[1]['name'],'General')
        self.assertEqual(0,len(landscape.landscapeItems[1]['items']))
        self.assertEqual(2,len(landscape.landscapeItems))
        self.assertEqual(1,len(landscape.landscapeItems[0]['items']))
        self.assertEqual(1,landscape.itemsAdded)
        self.assertEqual(2,landscape.itemsErrors)

    def testSyncItemInLandscape(self):
        members = LFXProjects(loadData=False,config=Config())
        
        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.com'
        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            member.logo = 'Gold.svg'
        member.membership = 'Premier Membership'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        member.repo_url = "https://github.com/foo/bar"
        member.second_path = ['Dog / Dog','Cat / Cat']
        member.extra['slug'] = 'testme'
        member.extra['artwork_url'] = 'https://google.com/art'
        members.members.append(member)

        testlandscape = """
landscape:
- category:
  name: Members
  subcategories:
  - subcategory:
    name: Premier
    items:
    - item:
      crunchbase: https://www.crunchbase.com/organization/here-technologies
      homepage_url: https://foo.com/
      logo: https://raw.githubusercontent.com/ucfoundation/ucf-landscape/master/hosted_logos/here.svg
      name: HERE Global B.V.
      twitter: https://twitter.com/here
      extra:
        slug: testme
"""
        with tempfile.NamedTemporaryFile(mode='w') as tmpfilename:
            tmpfilename.write(testlandscape)
            tmpfilename.flush()

            config = Config()
            config.landscapefile = os.path.basename(tmpfilename.name)
            config.basedir = os.path.dirname(tmpfilename.name)
            
            landscape = LandscapeOutput(config=config, resetCategory=False)
            with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
                landscape.syncItems(members)
            self.assertEqual(landscape.landscapeItems[0]['name'],'Premier')
            self.assertEqual(landscape.landscapeItems[0]['items'][0]['name'],"test")
            self.assertEqual(landscape.landscapeItems[0]['items'][0]['extra']['artwork_url'],"https://google.com/art")
            self.assertEqual(landscape.landscapeItems[0]['items'][0]['twitter'],"https://twitter.com/here")
            self.assertEqual(landscape.landscapeItems[0]['items'][0]['repo_url'],"https://github.com/foo/bar")
            self.assertIn('Dog / Dog',landscape.landscapeItems[0]['items'][0]['second_path'])
            self.assertIn('Cat / Cat',landscape.landscapeItems[0]['items'][0]['second_path'])
            self.assertEqual(1,landscape.itemsUpdated)

    def testLoadLandscapeReset(self):
        testlandscape = """
landscape:
- category:
  name: test me
  subcategories:
  - subcategory:
    name: Good
    items:
    - item:
      crunchbase: https://www.crunchbase.com/organization/here-technologies
      homepage_url: https://here.com/
      logo: https://raw.githubusercontent.com/ucfoundation/ucf-landscape/master/hosted_logos/here.svg
      name: HERE Global B.V.
      twitter: https://twitter.com/here
"""
        with tempfile.NamedTemporaryFile(mode='w') as tmpfilename:
            tmpfilename.write(testlandscape)
            tmpfilename.flush()

            config = Config()
            config.landscapeMembersCategory = 'test me'
            config.landscapeMembersSubcategories = [
                {"name": "Good Membership", "category": "Good"},
                {"name": "Bad Membership", "category": "Bad"}
                ]
            config.landscapefile = tmpfilename.name

            landscape = LandscapeOutput(config=config, resetCategory=True)
            
            self.assertEqual(landscape.landscape['landscape'][0]['name'],'test me')
            self.assertEqual(landscape.landscape['landscape'][0]['subcategories'][0]['name'],"Good")
            self.assertEqual(len(landscape.landscape['landscape'][0]['subcategories'][0]['items']),0)
            self.assertEqual(landscape.landscapeItems[0]['name'],"Good")

    def testLoadLandscapeEmpty(self):
        testlandscape = ""
        with tempfile.NamedTemporaryFile(mode='w') as tmpfilename:
            tmpfilename.write(testlandscape)
            tmpfilename.flush()

            config = Config()
            config.landscapeMembersCategory = 'test me'
            config.landscapeMembersSubcategories = [
                {"name": "Good Membership", "category": "Good"},
                {"name": "Bad Membership", "category": "Bad"}
                ]
            config.landscapefile = tmpfilename.name

            landscape = LandscapeOutput(config=config)

            self.assertEqual(landscape.landscape['landscape'][0]['name'],'test me')
            self.assertEqual(landscape.landscape['landscape'][0]['subcategories'][0]['name'],"Good")
            self.assertEqual(landscape.landscape['landscape'][0]['subcategories'][1]['name'],"Bad")

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("debug.log"),
        ]
    )
    
    unittest.main()
