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

    @unittest.mock.patch("lfx_landscape_tools.members.Members.__abstractmethods__", set())
    def testFind(self):
        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.com'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        members = Members(config=Config())
        members.members.append(member)

        self.assertTrue(members.find(member.orgname,member.website))
        self.assertTrue(members.find('dog',member.website))
        self.assertTrue(members.find(member.orgname,'https://bar.com'))

    @unittest.mock.patch("lfx_landscape_tools.members.Members.__abstractmethods__", set())
    def testFindFail(self):
        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.com'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        members = Members(config=Config())
        members.members.append(member)

        self.assertFalse(members.find('dog','https://bar.com'))

    @unittest.mock.patch("lfx_landscape_tools.members.Members.__abstractmethods__", set())
    def testFindMultiple(self):
        members = Members(config=Config())
        
        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.com'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        members.members.append(member)

        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.com'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        members.members.append(member)
        
        self.assertEqual(len(members.find(member.orgname,member.website)),2)
    
    @unittest.mock.patch("lfx_landscape_tools.members.Members.__abstractmethods__", set())
    def testNormalizeCompanyEmptyOrg(self):
        members = Members(config=Config(),loadData=False)
        self.assertEqual(members.normalizeCompany(None),'')

    @unittest.mock.patch("lfx_landscape_tools.members.Members.__abstractmethods__", set())
    def testNormalizeCompany(self):
        companies = [
            {"name":"Foo","normalized":"Foo"},
            {"name":"Foo Inc.","normalized":"Foo"}
        ]

        for company in companies:
            members = Members(config=Config(),loadData=False)
            self.assertEqual(members.normalizeCompany(company["name"]),company["normalized"])

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("debug.log"),
        ]
    )
    
    unittest.main()
