#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

import unittest
import responses
import requests
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

class TestTACAgendaProjects(unittest.TestCase):
    
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("debug.log",mode="w"),
        ]
    )
    
    def setUp(self):
        logging.getLogger().debug("Running {}".format(unittest.TestCase.id(self)))

    @unittest.mock.patch('subprocess.run')
    def testLoadData(self, mock_run):
        mock_result = unittest.mock.Mock()
        mock_result.stdout = '{"items":[{"assignees":["carolalynn"],"content":{"body":"","number":473,"repository":"AcademySoftwareFoundation/tac","title":"D&I Working Group","type":"Issue","url":"https://github.com/AcademySoftwareFoundation/tac/issues/473"},"id":"PVTI_lADOAm6tAs4AS_w4zgJSO7E","labels":["2-annual-review"],"landscape URL":"https://landscape.aswf.io/card-mode?project=working-group&selected=d-i-working-group","pCC Project ID":"a092M00001KWjDZQA1","pCC TSC Committee ID":"ac9cbe7f-0dc8-4be0-b404-cb7b9b0bb22f","repository":"https://github.com/AcademySoftwareFoundation/tac","scheduled Date":"2024-12-11","status":"Next Meeting Agenda Items","title":"D&I Working Group"},{"assignees":["carolalynn"],"content":{"body":"","number":473,"repository":"AcademySoftwareFoundation/tac","title":"D&I Working Group","type":"Issue","url":"https://github.com/AcademySoftwareFoundation/tac/issues/473"},"id":"PVTI_lADOAm6tAs4AS_w4zgJSO7E","labels":[],"landscape URL":"https://landscape.aswf.io/card-mode?project=working-group&selected=d-i-working-group","pCC Project ID":"a092M00001KWjDZQA1","pCC TSC Committee ID":"ac9cbe7f-0dc8-4be0-b404-cb7b9b0bb22f","repository":"https://github.com/AcademySoftwareFoundation/tac","scheduled Date":"2024-12-11","status":"Next Meeting Agenda Items","title":"D&I Working Group"}],"totalCount":32}'
        mock_run.return_value = mock_result

        config = Config()
        config.slug = 'aswf'
        config.projectsAddTechnologySector = True
        config.projectsAddIndustrySector = True
        config.projectsAddPMOManagedStatus = True
        config.projectsAddParentProject = True
        config.artworkRepoUrl = "https://artwork.aswf.io/projects/{slug}"
        config.tacAgendaProjectUrl = "https://github.com/orgs/AcademySoftwareFoundation/projects/19/views/1" 
        members = TACAgendaProject(config=config,loadData=False)
       
        with unittest.mock.patch('requests_cache.CachedSession', requests.Session):
            members.loadData()
        self.assertEqual(members.members[0].name,"D&I Working Group")
        self.assertEqual(len(members.members),1)
    
    @unittest.mock.patch('subprocess.run')
    def testLoadDataNoTACAgendaProject(self, mock_run):
        mock_result = unittest.mock.Mock()
        mock_result.stdout = '{"items":[{"assignees":["carolalynn"],"content":{"body":"","number":473,"repository":"AcademySoftwareFoundation/tac","title":"D&I Working Group","type":"Issue","url":"https://github.com/AcademySoftwareFoundation/tac/issues/473"},"id":"PVTI_lADOAm6tAs4AS_w4zgJSO7E","labels":["2-annual-review"],"landscape URL":"https://landscape.aswf.io/card-mode?project=working-group&selected=d-i-working-group","pCC Project ID":"a092M00001KWjDZQA1","pCC TSC Committee ID":"ac9cbe7f-0dc8-4be0-b404-cb7b9b0bb22f","repository":"https://github.com/AcademySoftwareFoundation/tac","scheduled Date":"2024-12-11","status":"Next Meeting Agenda Items","title":"D&I Working Group"}],"totalCount":32}'
        mock_run.return_value = mock_result

        config = Config()
        config.slug = 'aswf'
        config.projectsAddTechnologySector = True
        config.projectsAddIndustrySector = True
        config.projectsAddPMOManagedStatus = True
        config.projectsAddParentProject = True
        config.artworkRepoUrl = "https://artwork.aswf.io/projects/{slug}"
        members = TACAgendaProject(config=config,loadData=False)
       
        with self.assertLogs(level='ERROR') as cm:
            with unittest.mock.patch('requests_cache.CachedSession', requests.Session):
                members.loadData()
        
        self.assertEqual(cm.output, ['ERROR:root:Cannot find GitHub Project - ID: Org:'])        
        self.assertEqual(members.members,[])
    
    @unittest.mock.patch('subprocess.run')
    def testLoadDataInvalidJSONResponse(self, mock_run):
        mock_result = unittest.mock.Mock()
        mock_result.stdout = 'error 12121212'
        mock_result.stderr = 'foo'
        mock_run.return_value = mock_result

        config = Config()
        config.slug = 'aswf'
        config.projectsAddTechnologySector = True
        config.projectsAddIndustrySector = True
        config.projectsAddPMOManagedStatus = True
        config.projectsAddParentProject = True
        config.artworkRepoUrl = "https://artwork.aswf.io/projects/{slug}"
        config.tacAgendaProjectUrl = "https://github.com/orgs/AcademySoftwareFoundation/projects/19/views/1" 
        members = TACAgendaProject(config=config,loadData=False)
       
        with self.assertLogs(level='ERROR') as cm:
            with unittest.mock.patch('requests_cache.CachedSession', requests.Session):
                members.loadData()
        
        self.assertEqual(cm.output, ["ERROR:root:Invalid response from gh client: 'foo'"])
        self.assertEqual(members.members,[])

if __name__ == '__main__':
    unittest.main()
