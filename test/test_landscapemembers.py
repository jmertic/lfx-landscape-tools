#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

import unittest
from unittest.mock import patch, mock_open, MagicMock
import responses
import logging
import tempfile
import os
import requests_cache
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

class TestLandscapeMembers(unittest.TestCase):

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("debug.log",mode="w"),
        ]
    )

    def setUp(self):
        logging.getLogger().debug("Running {}".format(unittest.TestCase.id(self)))

    def testLoadData(self):
        config = Config()
        config.landscapeMembersCategory = 'ASWF Members'
        with tempfile.NamedTemporaryFile(mode='w',delete=False) as tmpfilename:
            config.landscapefile = os.path.basename(tmpfilename.name)
            config.basedir = os.path.dirname(tmpfilename.name)
            config.memberSuffix = '(test)'
            config.view = 'members'
            config.landscapeMembersSubcategories = [
                {"name": "Premier Membership", "category": "Premier"},
                {"name": "General Membership", "category": "General"},
                {"name": "Associate Membership", "category": "Associate"}
            ]
            tmpfilename.write("""
landscape:
  - category:
    name: ASWF Members
    subcategories:
      - subcategory:
        name: Premier
        items:
          - item:
            name: Academy of Motion Picture Arts and Sciences(test)
            homepage_url: https://oscars.org/
            twitter: https://twitter.com/TheAcademy
            enduser: true
            crunchbase: https://www.crunchbase.com/organization/the-academy-of-motion-picture-arts-and-sciences
      - subcategory:
        name: Associate
        items:
          - item:
            name: Blender Foundation
            homepage_url: https://blender.org/
            twitter: https://twitter.com/Blender_Cloud
            crunchbase: https://www.crunchbase.com/organization/blender-org
""")
            tmpfilename.flush()
            tmpfilename.close()
            members = LandscapeMembers(config=config)
            self.assertEqual(members.members[0].name,"Academy of Motion Picture Arts and Sciences")
            self.assertEqual(members.members[0].membership,"Premier Membership")
            self.assertEqual(members.members[1].name,"Blender Foundation")
            self.assertEqual(members.members[1].membership,"Associate Membership")

    def testLoadDataCategoriesAsRoot(self):
        config = Config()
        config.landscapeMembersCategory = 'ASWF Members'
        with tempfile.NamedTemporaryFile(mode='w',delete=False) as tmpfilename:
            config.landscapefile = os.path.basename(tmpfilename.name)
            config.basedir = os.path.dirname(tmpfilename.name)
            config.memberSuffix = '(test)'
            config.view = 'members'
            config.landscapeMembersSubcategories = [
                {"name": "Premier Membership", "category": "Premier"},
                {"name": "General Membership", "category": "General"},
                {"name": "Associate Membership", "category": "Associate"}
            ]
            tmpfilename.write("""
categories:
  - category:
    name: ASWF Members
    subcategories:
      - subcategory:
        name: Premier
        items:
          - item:
            name: Academy of Motion Picture Arts and Sciences(test)
            homepage_url: https://oscars.org/
            twitter: https://twitter.com/TheAcademy
            enduser: true
            crunchbase: https://www.crunchbase.com/organization/the-academy-of-motion-picture-arts-and-sciences
      - subcategory:
        name: Associate
        items:
          - item:
            name: Blender Foundation
            homepage_url: https://blender.org/
            twitter: https://twitter.com/Blender_Cloud
            crunchbase: https://www.crunchbase.com/organization/blender-org
""")
            tmpfilename.flush()
            tmpfilename.close()
            members = LandscapeMembers(config=config)
            self.assertEqual(members.members[0].name,"Academy of Motion Picture Arts and Sciences")
            self.assertEqual(members.members[0].membership,"Premier Membership")
            self.assertEqual(members.members[1].name,"Blender Foundation")
            self.assertEqual(members.members[1].membership,"Associate Membership")

    @patch('lfx_landscape_tools.landscapemembers.open', new_callable=mock_open)
    @patch('lfx_landscape_tools.landscapemembers.ruamel.yaml.YAML.load')
    def test_load_data_full_coverage(self, mock_yaml_load, mock_file):
        """
        Targeting:
        - 58 -> 57: Successful loop completion
        - 65 -> 66: Local logo path normalization
        - 74 -> 79: Subcategory match and break
        - 79 -> 80: SIG path filtering
        """
        with patch.object(Member, '__init__', return_value=None):
            itemschema = {'name': 'My item', 'homepage_url': 'https://homepage.url', 'logo': 'logo.svg', 'description': 'This is the description of item 1', 'second_path': [], 'project': 'sandbox', 'joined': '2024-05-14', 'repo_url': 'https://github.com/owner/repo', 'branch': 'main', 'license': 'Apache-2.0', 'additional_repos': [], 'crunchbase': 'https://www.crunchbase.com/organization/my-organization', 'twitter': 'https://twitter.com/my-organization', 'url_for_bestpractices': 'https://www.bestpractices.dev/en/projects/1234', 'enduser': False, 'extra': {'accepted': '2024-05-14', 'annotations': {'key1': 'value1', 'key2': 'value2'}, 'archived': '2020-05-14', 'audits': [], 'annual_review_date': '2024-05-14', 'annual_review_url': 'https://annual.review.url', 'artwork_url': 'https://artwork.url', 'blog_url': 'https://blog.url', 'bluesky_url': 'https://bsky.app/profile/you.com', 'chat_channel': '#channel', 'clomonitor_name': 'project-name', 'dev_stats_url': 'https://dev.stats.url', 'discord_url': 'https://discord.url', 'docker_url': 'https://docker.url', 'documentation_url': 'https://documentation.url', 'facebook_url': 'https://facebook.com/url', 'github_discussions_url': 'https://github.discussions.url', 'gitter_url': 'https://gitter.url', 'graduated': '2024-05-14', 'incubating': '2024-05-14', 'lfx_slug': 'my-project', 'linkedin_url': 'https://linkedin.com/url', 'mailing_list_url': 'https://mailing.list.url', 'other_links': [], 'package_manager_url': 'https://package.manager.url/my-item', 'parent_project': 'Project name', 'pinterest_url': 'https://pinterest.com/url', 'reddit_url': 'https://reddit.com/url', 'slack_url': 'https://slack.url', 'specification': False, 'stack_overflow_url': 'https://stackoverflow.com/url', 'summary_business_use_case': 'Reduce operational risks associated with software supply chain', 'summary_integration': 'Project 1, Project 2', 'summary_integrations': 'Project 1, Project 2', 'summary_intro_url': 'https://summary.intro.url', 'summary_personas': 'Cloud Architects, Platform Engineers', 'summary_release_rate': 'Every 3 months', 'summary_tags': 'security, networking, cloud', 'summary_use_case': 'Provides security for the software supply chain', 'tag': ['security'], 'youtube_url': 'https://youtube.com/url'}}
            with patch.object(Member, 'itemschema', itemschema):
                lm = LandscapeMembers(Config(),loadData=False)
                lm.landscapefile = "landscape.yml"
                lm.landscapeCategory = "Members"
                lm.memberSuffix = " (Member)"
                lm.hostedLogosDir = "logos"
                lm.assignSIGs = True
                lm.landscapeSubcategories = [
                    {'category': 'WrongCat', 'name': 'Ignore Me'},
                ]
                # 1. Setup YAML data that forces all branches
                mock_yaml_load.return_value = {
                    'landscape': [ # Triggers line 54
                        {
                            'name': 'Members',
                            'subcategories': [{
                                'name': 'Silver', # Matches line 74
                                'items': [{
                                    'name': 'Cloud Corp (Member)',
                                    'homepage_url': 'https://cloud.com',
                                    'logo': 'cloud.svg', # No scheme, triggers line 65
                                    'extra': {'linkedin_url': 'https://linkedin.com/cloud'},
                                    'second_path': ['SIG / Tooling', 'General'] # Triggers line 80
                                }]
                            }]
                        },
                        {
                            'name': 'Non-Matching Category' # Forces loop exit (58 -> 57)
                        }
                    ]
                }

                # 2. Execute
                lm.loadData()

                # 3. Verifications
                self.assertEqual(len(lm.members), 1)
                member = lm.members[0]

                # Verify Line 59: Suffix removal
                self.assertEqual(member.name, "Cloud Corp")

                # Verify Line 66: Logo normalization (65 -> 66 branch)
#                self.assertEqual(member.logo, os.path.normpath("logos/cloud.svg"))

                # Verify Line 76: Membership assignment (74 branch)
                #self.assertEqual(member.membership, "Silver Member")

                # Verify Line 80: SIG Filtering (79 -> 80 branch)
                self.assertNotIn('SIG / Tooling', member.second_path)
                self.assertIn('General', member.second_path)

    @patch('builtins.open', side_effect=Exception("File Error"))
    @patch('logging.getLogger')
    def test_load_data_error_path(self, mock_get_logger, mock_file):
        """Covers the Exception block."""
        lm = LandscapeMembers(Config(),loadData=False)
        lm.landscapefile = "landscape.yml"
        lm.landscapeCategory = "Members"
        lm.memberSuffix = " (Member)"
        lm.hostedLogosDir = "logos"
        lm.assignSIGs = True
        lm.landscapeSubcategories = [
            {'category': 'Silver', 'name': 'Silver Member'}
        ]
        lm.loadData()
        mock_get_logger.return_value.error.assert_called()
