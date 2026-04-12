#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

import unittest
from unittest.mock import patch, MagicMock
import responses
import logging

import requests
import ruamel.yaml

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

        members = Members(Config())
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

        members = Members(Config())
        members.members.append(member)

        self.assertFalse(members.find('dog','https://bar.com'))

    @unittest.mock.patch("lfx_landscape_tools.members.Members.__abstractmethods__", set())
    def testFindMultiple(self):
        members = Members(Config())

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

        members = Members(Config())
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

        members = Members(Config())
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

        members = Members(Config())
        members.members.append(member)

        self.assertFalse(members.find('dog','https://bar.com',member.membership))
        self.assertFalse(members.find(member.name,member.homepage_url,'Silver'))
        self.assertFalse(members.find('dog','https://bar.com',repo_url='https://github.com/bar/foo'))

    @unittest.mock.patch("lfx_landscape_tools.members.Members.__abstractmethods__", set())
    def test_find_complete_coverage(self):
        # Setup one member in the list
        mock_member = MagicMock()
        mock_member.name = "Linux Foundation"
        mock_member.homepage_url = "https://linuxfoundation.org"
        mock_member.membership = "Silver"
        mock_member.repo_url = "https://github.com/linuxfoundation"
        mock_member.extra = {}
        members_obj = Members(Config())
        members_obj.members = [mock_member]

        # --- Clear 66 -> 67 ---
        # Provide name and URL, but NO slug/membership/repo_url.
        # Forces entry into line 66 and makes it TRUE.
        found_members = members_obj.find(name="Linux Foundation", homepage_url="https://linuxfoundation.org")
        self.assertEqual("Linux Foundation",found_members[0].name)

        # --- Clear 70 -> 53 ---
        # Provide ONLY name. Forces logic to line 70.
        # Case A: Name does NOT match (Clears the False branch of line 70)
        self.assertEqual(members_obj.find(name="NonExistent Corp", homepage_url=None),[])
        self.assertEqual(members_obj.find(name=None, homepage_url=None),[])

        # --- Clear 71 -> 53 ---
        # Case B: Name DOES match (Clears the True branch of line 70 and line 71)
        found_members = members_obj.find(name="Linux Foundation", homepage_url=None)
        self.assertEqual("Linux Foundation",found_members[0].name)

    @unittest.mock.patch("lfx_landscape_tools.members.Members.__abstractmethods__", set())
    def testNormalizeNameEmptyOrg(self):
        members = Members(Config(),loadData=False)
        self.assertEqual(members.normalizeName(None),'')

    @unittest.mock.patch("lfx_landscape_tools.members.Members.__abstractmethods__", set())
    def testNormalizeName(self):
        companies = [
            {"name":"Foo","normalized":"Foo"},
            {"name":"Foo Inc.","normalized":"Foo"}
        ]

        for company in companies:
            members = Members(Config(),loadData=False)
            self.assertEqual(members.normalizeName(company["name"]),company["normalized"])

    @unittest.mock.patch("lfx_landscape_tools.members.Members.__abstractmethods__", set())
    def testOverlay(self):
        members1 = Members(Config())

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

        members2 = Members(Config())

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

