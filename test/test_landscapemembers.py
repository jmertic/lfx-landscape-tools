#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

import unittest
import responses
import logging
import tempfile
import os

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

if __name__ == '__main__':
    unittest.main()
