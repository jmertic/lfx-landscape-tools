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

class TestConfig(unittest.TestCase):
    
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("debug.log",mode="w"),
        ]
    )
    
    def setUp(self):
        logging.getLogger().debug("Running {}".format(unittest.TestCase.id(self)))

    def testLoadConfig(self):
        testconfigfilecontents = """
hostedLogosDir: 'hosted_logos'
landscapeMemberClasses:
   - name: Premier Membership
     category: Premier
   - name: General Membership
     category: General
   - name: Associate Membership
     category: Associate
project: a09410000182dD2AAI # Academy Software Foundation
slug: aswf
landscapeMemberCategory: ASWF Member Company
memberSuffix: " (help)"
"""
        tmpfilename = tempfile.NamedTemporaryFile(mode='w',delete=False)
        tmpfilename.write(testconfigfilecontents)
        tmpfilename.close()

        with open(tmpfilename.name) as fp:
            config = Config(fp)

            self.assertEqual(config.project,"a09410000182dD2AAI")
            self.assertEqual(config.landscapeCategory,"ASWF Member Company")
            self.assertEqual(config.landscapefile,"landscape.yml")
            self.assertEqual(config.missingcsvfile,"missing.csv")
            self.assertEqual(config.landscapeSubcategories[0]['name'],"Premier Membership")
            self.assertEqual(config.memberSuffix," (help)")

        os.unlink(tmpfilename.name)

    def testLoadConfigMissingCsvFileLandscapeFile(self):
        testconfigfilecontents = """
project: a09410000182dD2AAI # Academy Software Foundation
slug: aswf
landscapefile: foo.yml
missingcsvfile: foo.csv
"""
        tmpfilename = tempfile.NamedTemporaryFile(mode='w',delete=False)
        tmpfilename.write(testconfigfilecontents)
        tmpfilename.close()

        with open(tmpfilename.name) as fp:
            config = Config(fp)

            self.assertEqual(config.project,"a09410000182dD2AAI")
            self.assertEqual(config.landscapefile,"foo.yml")
            self.assertEqual(config.missingcsvfile,"foo.csv")

        os.unlink(tmpfilename.name)
    
    def testLoadConfigDefaults(self):
        testconfigfilecontents = """
project: a09410000182dD2AAI # Academy Software Foundation
slug: aswf
"""
        tmpfilename = tempfile.NamedTemporaryFile(mode='w',delete=False)
        tmpfilename.write(testconfigfilecontents)
        tmpfilename.close()

        with open(tmpfilename.name) as fp:
            config = Config(fp)

            self.assertEqual(config.landscapeCategory,'Members')
            self.assertEqual(config.landscapeSubcategories,[
                {"name": "Premier Membership", "category": "Premier"},
                {"name": "General Membership", "category": "General"},
            ])
            self.assertEqual(config.landscapefile,'landscape.yml')
            self.assertEqual(config.missingcsvfile,'missing.csv')
            self.assertEqual(config.hostedLogosDir,'hosted_logos')
            self.assertEqual(config.memberSuffix,'')
            self.assertEqual(config.project,"a09410000182dD2AAI")

        os.unlink(tmpfilename.name)

    def testLoadConfigDefaultsNotSet(self):
        testconfigfilecontents = """
projectewew: a09410000182dD2AAI # Academy Software Foundation
"""
        tmpfilename = tempfile.NamedTemporaryFile(mode='w',delete=False)
        tmpfilename.write(testconfigfilecontents)
        tmpfilename.close()

        with open(tmpfilename.name) as fp:
            with self.assertRaises(ValueError, msg="'project' not defined in config file"):
                config = Config(fp)

        os.unlink(tmpfilename.name)

    def testLoadProjectsConfig(self):
        testconfigfilecontents = """
landscapeName: lfenergy
landscapeMemberClasses:
  - name: Strategic Membership
    category: Strategic
  - name: Premier Membership
    category: Strategic
  - name: General Membership
    category: General
  - name: Associate Membership
    category: Associate
project: a094100001Cb6HaAAJ # LF Energy Foundation
slug: lfenergy
landscapeMemberCategory: LF Energy Member
landscapeProjectsCategory: LF Energy Projects
landscapeProjectsSubcategories:
  - name: All
    category: All
landscapefile: landscape.yml
memberSuffix: ' (member)'
missingcsvfile: missing.csv
"""
        tmpfilename = tempfile.NamedTemporaryFile(mode='w',delete=False)
        tmpfilename.write(testconfigfilecontents)
        tmpfilename.close()

        with open(tmpfilename.name) as fp:
            config = Config(fp,view='projects')

            self.assertEqual(config.project,"a094100001Cb6HaAAJ")
            self.assertEqual(config.landscapeCategory,"LF Energy Projects")
            self.assertEqual(config.landscapefile,"landscape.yml")
            self.assertEqual(config.missingcsvfile,"missing.csv")
            self.assertEqual(config.landscapeSubcategories[0]['name'],"All")
            self.assertEqual(config.memberSuffix," (member)")

        os.unlink(tmpfilename.name)

    def testLoadUndefinedConfig(self):
        testconfigfilecontents = """
landscapeName: lfenergy
landscapeMemberClasses:
  - name: Strategic Membership
    category: Strategic
  - name: Premier Membership
    category: Strategic
  - name: General Membership
    category: General
  - name: Associate Membership
    category: Associate
project: a094100001Cb6HaAAJ # LF Energy Foundation
slug: lfenergy
landscapeMemberCategory: LF Energy Member
landscapeProjectsCategory: LF Energy Projects
landscapeProjectsSubcategories:
  - name: All
    category: All
landscapefile: landscape.yml
memberSuffix: ' (member)'
missingcsvfile: missing.csv
"""
        tmpfilename = tempfile.NamedTemporaryFile(mode='w',delete=False)
        tmpfilename.write(testconfigfilecontents)
        tmpfilename.close()

        with open(tmpfilename.name) as fp:
            config = Config(fp,view='undefined')
            
            self.assertEqual(config.view,Config.view)

        os.unlink(tmpfilename.name)

    @responses.activate
    def testLookupSlugByProjectID(self):

        responses.add(
            method=responses.GET,
            url='https://api-gw.platform.linuxfoundation.org/project-service/v1/public/projects?slug=aswf',
            json={
                "Data": [
                    {
                        "AutoJoinEnabled": True,
                        "Description": "The mission of the Academy Software Foundation (ASWF) is to increase the quality and quantity of contributions to the content creation industry’s open source software base; to provide a neutral forum to coordinate cross-project efforts; to provide a common build and test infrastructure; and to provide individuals and organizations a clear path to participation in advancing our open source ecosystem.",
                        "DisplayOnhomepage_url": True,
                        "HasProgramManager": True,
                        "Industry": [
                            "Motion Pictures"
                        ],
                        "IndustrySector": "Motion Pictures",
                        "Model": [
                            "Membership"
                        ],
                        "Name": "Academy Software Foundation (ASWF)",
                        "ProjectID": "a09410000182dD2AAI",
                        "ProjectLogo": "https://lf-master-project-logos-prod.s3.us-east-2.amazonaws.com/aswf.svg",
                        "ProjectType": "Project Group",
                        "RepositoryURL": "https://github.com/academysoftwarefoundation",
                        "Slug": "aswf",
                        "StartDate": "2018-08-10",
                        "Status": "Active",
                        "TechnologySector": "Visual Effects",
                        "TestRecord": False,
                        "homepage_url": "https://www.aswf.io/"
                    }
                ],
                "Metadata": {
                    "Offset": 0,
                    "PageSize": 100,
                    "TotalSize": 1
                }
            })

        testconfigfilecontents = """
slug: aswf
"""
        tmpfilename = tempfile.NamedTemporaryFile(mode='w',delete=False)
        tmpfilename.write(testconfigfilecontents)
        tmpfilename.close()

        with open(tmpfilename.name) as fp:
            config = Config(fp)

            self.assertEqual(config.slug,'aswf')
            self.assertEqual(config.project,"a09410000182dD2AAI")

        os.unlink(tmpfilename.name)

if __name__ == '__main__':
    unittest.main()
