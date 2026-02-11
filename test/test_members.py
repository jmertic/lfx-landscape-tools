#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

import unittest
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

class TestMembers(unittest.TestCase):
    
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("debug.log",mode="w"),
        ]
    )
    
    def setUp(self):
        logging.getLogger().debug("Running {}".format(unittest.TestCase.id(self)))

    @unittest.mock.patch("lfx_landscape_tools.members.Members.__abstractmethods__", set())
    def testFind(self):
        member = Member()
        member.name = 'test'
        member.homepage_url = 'https://foo.com'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        members = Members(config=Config())
        members.members.append(member)

        self.assertTrue(members.find(member.name,member.homepage_url))
        self.assertTrue(members.find('dog',member.homepage_url))
        self.assertTrue(members.find(member.name,'https://bar.com'))

    @unittest.mock.patch("lfx_landscape_tools.members.Members.__abstractmethods__", set())
    def testFindFail(self):
        member = Member()
        member.name = 'test'
        member.homepage_url = 'https://foo.com'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        members = Members(config=Config())
        members.members.append(member)

        self.assertFalse(members.find('dog','https://bar.com'))

    @unittest.mock.patch("lfx_landscape_tools.members.Members.__abstractmethods__", set())
    def testFindMultiple(self):
        members = Members(config=Config())
        
        member = Member()
        member.name = 'test'
        member.homepage_url = 'https://foo.com'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        members.members.append(member)

        member = Member()
        member.name = 'test'
        member.homepage_url = 'https://foo.com'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        members.members.append(member)
        
        self.assertEqual(len(members.find(member.name,member.homepage_url)),2)
    
    @unittest.mock.patch("lfx_landscape_tools.members.Members.__abstractmethods__", set())
    def testFindBySlug(self):
        member = Member()
        member.name = 'test'
        member.homepage_url = 'https://foo.com'
        member.extra = {'lfx_slug':'aswf'}

        members = Members(config=Config())
        members.members.append(member)

        self.assertEqual(members.find(name=member.name,homepage_url='https://bar.com',slug='aswf')[0].name,'test')
        self.assertTrue(members.find(member.name,'https://bar.com',repo_url=member.repo_url))
    
    @unittest.mock.patch("lfx_landscape_tools.members.Members.__abstractmethods__", set())
    def testFindByMembership(self):
        member = Member()
        member.name = 'test'
        member.homepage_url = 'https://foo.com'
        with unittest.mock.patch("lfx_landscape_tools.svglogo.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            member.logo = 'Gold.svg'
        member.membership = 'Gold'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        member.repo_url = "https://github.com/foo/bar"

        members = Members(config=Config())
        members.members.append(member)

        self.assertTrue(members.find(name=member.name,homepage_url=member.homepage_url))
        self.assertTrue(members.find(name=member.name,homepage_url=member.homepage_url,membership=member.membership))
        self.assertTrue(members.find(name='dog',homepage_url=member.homepage_url,membership=member.membership))
        self.assertTrue(members.find(name=member.name,homepage_url='https://bar.com',membership=member.membership))
        self.assertTrue(members.find(name=member.name,homepage_url='https://bar.com',repo_url=member.repo_url))

    @unittest.mock.patch("lfx_landscape_tools.members.Members.__abstractmethods__", set())
    def testFindByMembershipFail(self):
        member = Member()
        member.name = 'test'
        member.homepage_url = 'https://foo.com'
        with unittest.mock.patch("lfx_landscape_tools.svglogo.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            member.logo = 'Gold.svg'
        member.membership = 'Gold'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        member.repo_url = "https://github.com/foo/bar"

        members = Members(config=Config())
        members.members.append(member)

        self.assertFalse(members.find('dog','https://bar.com',member.membership))
        self.assertFalse(members.find(member.name,member.homepage_url,'Silver'))
        self.assertFalse(members.find('dog','https://bar.com',repo_url='https://github.com/bar/foo'))
    
    @unittest.mock.patch("lfx_landscape_tools.members.Members.__abstractmethods__", set())
    def testNormalizeNameEmptyOrg(self):
        members = Members(config=Config(),loadData=False)
        self.assertEqual(members.normalizeName(None),'')

    @unittest.mock.patch("lfx_landscape_tools.members.Members.__abstractmethods__", set())
    def testNormalizeName(self):
        companies = [
            {"name":"Foo","normalized":"Foo"},
            {"name":"Foo Inc.","normalized":"Foo"}
        ]

        for company in companies:
            members = Members(config=Config(),loadData=False)
            self.assertEqual(members.normalizeName(company["name"]),company["normalized"])
    
    @unittest.mock.patch("lfx_landscape_tools.members.Members.__abstractmethods__", set())
    def testOverlay(self):
        members1 = Members(config=Config())
        
        member = Member()
        member.name = 'test1'
        member.homepage_url = 'https://foo.com'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        members1.members.append(member)

        member = Member()
        member.name = 'test2'
        member.homepage_url = 'https://foo2.com'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        members1.members.append(member)

        member = Member()
        member.name = 'weirdtest'
        member.extra = {'lfx_slug':'test3'}
        member.homepage_url = 'https://foo2.com'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        members1.members.append(member)
        
        members2 = Members(config=Config())
        
        member = Member()
        member.name = 'test1'
        member.homepage_url = 'https://foo1.com'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        members2.members.append(member)

        member = Member()
        member.name = 'test3'
        member.homepage_url = 'https://foo3.com'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        member.extra = {'lfx_slug':'test3'}
        members2.members.append(member)
        
        members1.overlay(members2)

        self.assertEqual(len(members1.members),3)
        self.assertEqual(members1.members[0].name,'test1')
        self.assertEqual(members1.members[0].homepage_url,'https://foo1.com/')
        self.assertEqual(members1.members[1].name,'test2')
        self.assertEqual(members1.members[2].name,'test3')

if __name__ == '__main__':
    unittest.main()
