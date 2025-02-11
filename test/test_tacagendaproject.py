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
import os

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
        with open("{}/data.yml".format(os.path.dirname(__file__)), 'r', encoding="utf8", errors='ignore') as fileobject:   
            responses.get('https://raw.githubusercontent.com/cncf/landscape2/refs/heads/main/docs/config/data.yml', body=fileobject.read())
        responses.add(
            method=responses.GET,
            url="https://api-gw.platform.linuxfoundation.org/project-service/v1/public/projects?$filter=projectId%20eq%20a092M00001KWjDZQA1",
            json={
                "Data": [
                    {
                        "AutoJoinEnabled": False,
                        "Category": "Working Group",
                        "Description": "The purpose of this Working Group is to create a cross-industry effort to encourage diversity and inclusion across the open source software ecosystem for vfx and animation. The WG will bring together software engineers/developers, marketing/communications professionals, HR, and anyone else passionate about D&I within vfx and animation.",
                        "DisplayOnWebsite": True,
                        "HasProgramManager": False,
                        "Industry": [
                            "Motion Pictures"
                        ],
                        "IndustrySector": "Motion Pictures",
                        "Name": "Diversity & Inclusion Working Group",
                        "ParentID": "a09410000182dD2AAI",
                        "ParentSlug": "aswf",
                        "ProjectID": "a092M00001KWjDZQA1",
                        "ProjectLogo": "https://lfx-cdn-prod.s3.us-east-1.amazonaws.com/project-artifacts/diversity-inclusion-wg/diversity-inclusion-wg-logo.svg?v=1723243760311",
                        "ProjectType": "Project",
                        "Slug": "aswf-diversity-inclusion-wg",
                        "StartDate": "2020-06-11",
                        "Status": "Active",
                        "TechnologySector": "Cross-Technology",
                        "TestRecord": False,
                        "Website": "https://lists.aswf.io/g/diversity"
                    }
                ],
                "Metadata": {
                    "Offset": 0,
                    "PageSize": 100,
                    "TotalSize": 1
                }
            })

        responses.add(
            method=responses.GET,
            url="https://api-gw.platform.linuxfoundation.org/project-service/v2/public/projects/a092M00001KWjDZQA1/committees/ac9cbe7f-0dc8-4be0-b404-cb7b9b0bb22f/members",
            json={
                "Data": [
                    {
                        "AppointedBy": "Community",
                        "FirstName": "Carol",
                        "LastName": "Payne",
                        "Role": "Chair",
                        "Status": "Active",
                        "VotingStatus": "Voting Rep",
                        "MemberID": "0032M00002zw7ygQAA",
                        "OrganizationID": "0014100000Te0QpAAJ",
                        "AboutMe": {
                            "Description": "Color & Imaging Workflow Leader. OCIO TSC Chair, D&I Working Group Co-Chair. ",
                            "GitHub": "https://github.com/carolalynn22",
                            "LinkedIn": "https://linkedin.com/in/carolalynn"
                        },
                        "CreatedDate": "2023-09-07T20:28:56.281Z",
                        "ID": "95d6004c-0bae-4b9d-903d-8d6ae17112c5",
                        "LogoURL": "https://platform-logos-myprofile-api-prod.s3.us-east-2.amazonaws.com/carolalynn.png?v=1714481231547",
                        "Organization": {
                            "ID": "0014100000Te0QpAAJ",
                            "LogoURL": "https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/netflix.svg",
                            "Name": "Netflix, Inc."
                        },
                        "SystemModStamp": "2023-09-07T20:29:03.075Z",
                        "Title": "Imaging Technologist",
                        "Twitter": "https://twitter.com/carolalynn"
                    },
                    {
                        "AppointedBy": "Community",
                        "FirstName": "Rachel",
                        "LastName": "Rose",
                        "Role": "Chair",
                        "Status": "Active",
                        "VotingStatus": "Voting Rep",
                        "MemberID": "0032M00002zuzoKQAQ",
                        "OrganizationID": "0012M00002KB7YbQAL",
                        "AboutMe": {
                            "GitHub": "https://github.com/rachelmrose",
                            "LinkedIn": "https://www.linkedin.com/in/rachel-rose-6905a12/"
                        },
                        "CreatedDate": "2023-09-07T20:28:56.030Z",
                        "ID": "dede07bf-6add-4fc0-b630-0abe1d81d4f9",
                        "LogoURL": "https://s.gravatar.com/avatar/10642bbd294cba10abaddcf643c47e45?s=480&r=pg&d=https%3A%2F%2Fcdn.auth0.com%2Favatars%2Frr.png",
                        "Organization": {
                            "ID": "0012M00002KB7YbQAL",
                            "LogoURL": "https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/IndustrialLightMagic.svg",
                            "Name": "Industrial Light & Magic"
                        },
                        "SystemModStamp": "2024-08-22T12:43:11.758Z",
                        "Title": "R&D Supervisor"
                    }
                ],
                "Metadata": {
                    "Offset": 0,
                    "PageSize": 100,
                    "TotalSize": 2
                }
            })

    @responses.activate
    @unittest.mock.patch('subprocess.run')
    def testLoadData(self, mock_run):
        mock_result = unittest.mock.Mock()
        mock_result.stdout = '{"items":[{"assignees":["carolalynn"],"content":{"body":"","number":473,"repository":"AcademySoftwareFoundation/tac","title":"D&I Working Group","type":"Issue","url":"https://github.com/AcademySoftwareFoundation/tac/issues/473"},"id":"PVTI_lADOAm6tAs4AS_w4zgJSO7E","labels":["2-annual-review"],"pCC TSC Committee URL":"https://projectadmin.lfx.linuxfoundation.org/project/a092M00001KWjDZQA1/collaboration/committees/ac9cbe7f-0dc8-4be0-b404-cb7b9b0bb22f","repository":"https://github.com/AcademySoftwareFoundation/tac","scheduled Date":"2024-12-11","status":"Next Meeting Agenda Items","title":"D&I Working Group"},{"assignees":["carolalynn"],"content":{"body":"","number":473,"repository":"AcademySoftwareFoundation/tac","title":"D&I Working Group","type":"Issue","url":"https://github.com/AcademySoftwareFoundation/tac/issues/473"},"id":"PVTI_lADOAm6tAs4AS_w4zgJSO7E","labels":[],"landscape URL":"https://landscape.aswf.io/card-mode?project=working-group&selected=d-i-working-group","pCC Project ID":"a092M00001KWjDZQA1","pCC TSC Committee ID":"ac9cbe7f-0dc8-4be0-b404-cb7b9b0bb22f","repository":"https://github.com/AcademySoftwareFoundation/tac","scheduled Date":"2024-12-11","status":"Next Meeting Agenda Items","title":"D&I Working Group"}],"totalCount":32}'
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
