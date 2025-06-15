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

class TestLFXProjects(unittest.TestCase):
    
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
        
        with open("{}/github_openassetio_response.html".format(os.path.dirname(__file__)), 'r', encoding="utf8", errors='ignore') as fileobject:
            responses.get("https://api.github.com:443/search/repositories?sort=stars&order=desc&q=org%3AOpenAssetIO&per_page=1000",body=fileobject.read())
        
    @responses.activate
    def testLoadData(self):
        config = Config()
        config.slug = 'aswf'
        config.projectsAddTechnologySector = True
        config.projectsAddIndustrySector = True
        config.projectsAddPMOManagedStatus = True
        config.projectsAddParentProject = True
        config.artworkRepoUrl = "https://artwork.aswf.io/projects/{slug}"
        members = LFXProjects(config=config,loadData=False)


        responses.add(
            method=responses.GET,
            url=members.singleSlugEndpointUrl.format(slug='aswfs'),
            json={
              "Data": [ ],
              "Metadata": {
                "Offset": 0,
                "PageSize": 100,
                "TotalSize": 0
              }
            })
        responses.add(
            method=responses.GET,
            url=members.singleSlugEndpointUrl.format(slug=members.project),
            json={
                "Data": [
                    {
                        "AutoJoinEnabled": True,
                        "Description": "The mission of the Academy Software Foundation (ASWF) is to increase the quality and quantity of contributions to the content creation industry’s open source software base; to provide a neutral forum to coordinate cross-project efforts; to provide a common build and test infrastructure; and to provide individuals and organizations a clear path to participation in advancing our open source ecosystem.",
                        "DisplayOnWebsite": True,
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
                        "Website": "https://www.aswf.io/"
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
            url=members.endpointURL.format(members.project),
            json={
                "Data": [
                    {
                        "AutoJoinEnabled": False,
                        "Description": "OpenCue is an open source render management system. You can use OpenCue in visual effects and animation production to break down complex jobs into individual tasks. You can submit jobs to a configurable dispatch queue that allocates the necessary computational resources.",
                        "Category": "Adopted",
                        "DisplayOnWebsite": True,
                        "HasProgramManager": False,
                        "Industry": [
                            "Motion Pictures"
                        ],
                        "IndustrySector": "Motion Pictures",
                        "Facebook": "https://www.facebook.com/TheLinuxFoundation",
                        "LinkedIn": "https://www.linkedin.com/company/208777",
                        "Reddit": "https://www.reddit.com/r/vfx/",
                        "Pinterest": "https://www.pinterest.com/linuxfoundation/",
                        "YouTube": "https://www.youtube.com/user/TheLinuxFoundation",
                        "Name": "OpenCue",
                        "ParentID": "a09410000182dD2AAI",
                        "ParentSlug": "aswf",
                        "ProjectID": "a092M00001IV3znQAD",
                        "ProjectLogo": "https://lf-master-project-logos-prod.s3.us-east-2.amazonaws.com/opencue.svg",
                        "ProjectType": "Project",
                        "RepositoryURL": "https://github.com/AcademySoftwareFoundation/OpenCue",
                        "Slug": "opencue",
                        "StartDate": "2020-04-24",
                        "Status": "Active",
                        "TechnologySector": "DevOps, CI/CD & Site Reliability;Web & Application Development;Visual Effects",
                        "TestRecord": False,
                        "Website": "https://opencue.io"
                    },
                    {
                        "AutoJoinEnabled": False,
                        "Description": "OpenTimelineIO (OTIO) is an API and interchange format for editorial cut information. You can think of it as a modern Edit Decision List (EDL) that also includes an API for reading, writing, and manipulating editorial data. It also includes a plugin system for translating to/from existing editorial formats as well as a plugin system for linking to proprietary media storage schemas.",
                        "DisplayOnWebsite": True,
                        "Category": "Incubating",
                        "HasProgramManager": True,
                        "Industry": [
                            "Motion Pictures"
                        ],
                        "IndustrySector": "Motion Pictures",
                        "Name": "OpenTimelineIO",
                        "ParentID": "a09410000182dD2AAI",
                        "ParentSlug": "aswfs",
                        "ProjectID": "a092M00001If9uZQAR",
                        "ProjectLogo": "https://lf-master-project-logos-prod.s3.us-east-2.amazonaws.com/open-timeline-io.svg",
                        "ProjectType": "Project",
                        "RepositoryURL": "https://github.com/PixarAnimationStudios/OpenTimelineIO",
                        "Slug": "open-timeline-io",
                        "StartDate": "2021-03-08",
                        "Status": "Active",
                        "TechnologySector": "Web & Application Development;Visual Effects",
                        "TestRecord": False,
                    },
                    {
                        "AutoJoinEnabled": False,
                        "Description": "The goal of the OpenEXR project is to keep the format reliable and modern and to maintain its place as the preferred image format for entertainment content creation.",
                        "DisplayOnWebsite": True,
                        "Category": "Adopted",
                        "HasProgramManager": False,
                        "Industry": [
                            "Motion Pictures"
                        ],
                        "IndustrySector": "Motion Pictures",
                        "Name": "OpenEXR",
                        "ParentID": "a09410000182dD2AAI",
                        "ParentSlug": "aswf",
                        "ProjectID": "a092M00001If9ujQAB",
                        "ProjectType": "Project",
                        "Slug": "openexr",
                        "StartDate": "2020-04-24",
                        "Status": "Active",
                        "TechnologySector": "Web & Application Development;Visual Effects",
                        "TestRecord": False,
                    },
                    {
                        "AutoJoinEnabled": False,
                        "Description": "The mission of the Project is to develop an open-source interoperability standard for tools and content management systems used in media production.",
                        "DisplayOnWebsite": True,
                        "Category": "Sandbox",
                        "HasProgramManager": False,
                        "Industry": [
                            "Motion Pictures"
                        ],
                        "IndustrySector": "",
                        "Name": "OpenAssetIO",
                        "ParentID": "a09410000182dD2AAI",
                        "ProjectID": "a092M00001L17vCQAR",
                        "ProjectLogo": "https://lf-master-project-logos-prod.s3.us-east-2.amazonaws.com/openassetio.svg",
                        "ProjectType": "Project",
                        "RepositoryURL": "https://github.com/OpenAssetIO",
                        "Slug": "openassetio",
                        "StartDate": "2022-11-01",
                        "Status": "Active",
                        "TechnologySector": "Visual Effects",
                        "TestRecord": False,
                        "Twitter": "https://yahoo.com",
                        "Website": "openassetio.org"
                    },
                    {
                        "AutoJoinEnabled": False,
                        "Description": "The mission of the Project is to develop an open-source interoperability standard for tools and content management systems used in media production.",
                        "DisplayOnWebsite": True,
                        "HasProgramManager": False,
                        "Industry": [
                            "Motion Pictures"
                        ],
                        "IndustrySector": "",
                        "Name": "OpenAssetIO",
                        "ParentID": "a09410000182dD2AAI",
                        "ProjectID": "a092M00001L17vCQAR",
                        "ProjectLogo": "https://lf-master-project-logos-prod.s3.us-east-2.amazonaws.com/openassetio.svg",
                        "ProjectType": "Project",
                        "RepositoryURL": "https://github.com/OpenAssetIO",
                        "Slug": "openassetio",
                        "StartDate": "2022-11-01",
                        "Status": "Active",
                        "TechnologySector": "Visual Effects",
                        "TestRecord": False,
                        "Website": "openassetio.org"
                    },
                    {
                        "AutoJoinEnabled": True,
                        "Description": "The mission of the Academy Software Foundation (ASWF) is to increase the quality and quantity of contributions to the content creation industry’s open source software base; to provide a neutral forum to coordinate cross-project efforts; to provide a common build and test infrastructure; and to provide individuals and organizations a clear path to participation in advancing our open source ecosystem.",
                        "DisplayOnWebsite": True,
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
                        "Website": "https://www.aswf.io/"
                    }
                ],
                "Metadata": {
                    "Offset": 0,
                    "PageSize": 100,
                    "TotalSize": 3
                }
            })
        responses.add(
            method=responses.GET,
            url="https://lf-master-project-logos-prod.s3.us-east-2.amazonaws.com/aswf.svg",
            body="""<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="21.88 16.88 864.24 167.74"><title>Hitachi, Ltd. logo</title><g fill="#231f20" fill-opacity="1" fill-rule="nonzero" stroke="none" transform="matrix(1.33333 0 0 -1.33333 0 204.84) scale(.1)"><path d="M5301.18 1258.82V875.188h513.3c0-1.372-.43 383.632 0 383.632h254.16s.9-958.422 0-959.461h-254.16V721.57c0-1.25-513.3 0-513.3 0 .45-1.621 0-422.461 0-422.211h-254.12s1.6 959.461 0 959.461h254.12"/><path d="M2889.38 1258.82v-163.28h-388.51V299.359h-254.16v796.181h-388.48s.52 163.16 0 163.28c.52-.12 1031.15 0 1031.15 0"/><path d="M3877.23 299.359h-282.89c.42 0-83.32 206.289-83.32 206.289h-476.2s-81.72-206.519-83.17-206.289c.19-.23-282.82 0-282.82 0l448.28 959.461c0-.64 311.7 0 311.7 0zm-604.28 796.181l-176.76-436.216h353.76l-177 436.216"/><path d="M6269.85 299.359h254.3v959.461h-254.3V299.359"/><path d="M544.422 1258.82s-.137-386.449 0-383.632h512.968c0-1.372-.15 383.632 0 383.632h254.32s.63-958.422 0-959.461h-254.32V721.57c0-1.25-512.968 0-512.968 0 .109-1.621-.137-422.461 0-422.211H290.223s1.425 959.461 0 959.461h254.199"/><path d="M1513.27 299.359h253.93v959.461h-253.93V299.359"/><path d="M3868.11 565.32c-22.26 64.336-34.24 132.27-34.24 204.239 0 100.742 17.93 198.476 66.25 279.391 49.59 83.52 125.86 148.17 218.05 182.62 87.95 32.89 182.36 51.07 281.6 51.07 114.14 0 222.29-25.05 320.69-67.71 91.64-39.25 160.88-122.01 181.25-221.735 4.08-19.652 7.42-40.097 9.12-60.55h-266.68c-1.04 25.375-5.18 50.898-13.97 73.845-20.09 53.07-64.22 94.21-119.1 110.87-35.29 10.84-72.58 16.58-111.31 16.58-44.24 0-86.58-7.8-125.8-21.74-65.04-22.77-115.88-75.55-138.65-140.63-22.25-63.203-35-131.304-35-202.011 0-58.438 9.51-114.922 24.51-168.438 19.12-70.019 71.62-126.051 138.62-151.461 42.57-15.941 88.26-25.469 136.32-25.469 41.02 0 80.35 6.289 117.6 18.297 49.57 15.703 90.02 52.481 111.06 99.551 14.02 31.469 20.87 66.27 20.87 103.051H4917c-1.52-31.117-5.8-62.133-12.83-91.098-22.83-94.863-89.32-174.371-177.68-211.621-100.54-42.242-210.54-66.699-326.72-66.699-89.92 0-176.48 14.219-257.73 39.668-123.97 39.199-231.31 128.398-273.93 249.98"/></g></svg>""")
        responses.add(
            method=responses.GET,
            url="https://lf-master-project-logos-prod.s3.us-east-2.amazonaws.com/openassetio.svg",
            body="""<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="21.88 16.88 864.24 167.74"><title>Hitachi, Ltd. logo</title><g fill="#231f20" fill-opacity="1" fill-rule="nonzero" stroke="none" transform="matrix(1.33333 0 0 -1.33333 0 204.84) scale(.1)"><path d="M5301.18 1258.82V875.188h513.3c0-1.372-.43 383.632 0 383.632h254.16s.9-958.422 0-959.461h-254.16V721.57c0-1.25-513.3 0-513.3 0 .45-1.621 0-422.461 0-422.211h-254.12s1.6 959.461 0 959.461h254.12"/><path d="M2889.38 1258.82v-163.28h-388.51V299.359h-254.16v796.181h-388.48s.52 163.16 0 163.28c.52-.12 1031.15 0 1031.15 0"/><path d="M3877.23 299.359h-282.89c.42 0-83.32 206.289-83.32 206.289h-476.2s-81.72-206.519-83.17-206.289c.19-.23-282.82 0-282.82 0l448.28 959.461c0-.64 311.7 0 311.7 0zm-604.28 796.181l-176.76-436.216h353.76l-177 436.216"/><path d="M6269.85 299.359h254.3v959.461h-254.3V299.359"/><path d="M544.422 1258.82s-.137-386.449 0-383.632h512.968c0-1.372-.15 383.632 0 383.632h254.32s.63-958.422 0-959.461h-254.32V721.57c0-1.25-512.968 0-512.968 0 .109-1.621-.137-422.461 0-422.211H290.223s1.425 959.461 0 959.461h254.199"/><path d="M1513.27 299.359h253.93v959.461h-253.93V299.359"/><path d="M3868.11 565.32c-22.26 64.336-34.24 132.27-34.24 204.239 0 100.742 17.93 198.476 66.25 279.391 49.59 83.52 125.86 148.17 218.05 182.62 87.95 32.89 182.36 51.07 281.6 51.07 114.14 0 222.29-25.05 320.69-67.71 91.64-39.25 160.88-122.01 181.25-221.735 4.08-19.652 7.42-40.097 9.12-60.55h-266.68c-1.04 25.375-5.18 50.898-13.97 73.845-20.09 53.07-64.22 94.21-119.1 110.87-35.29 10.84-72.58 16.58-111.31 16.58-44.24 0-86.58-7.8-125.8-21.74-65.04-22.77-115.88-75.55-138.65-140.63-22.25-63.203-35-131.304-35-202.011 0-58.438 9.51-114.922 24.51-168.438 19.12-70.019 71.62-126.051 138.62-151.461 42.57-15.941 88.26-25.469 136.32-25.469 41.02 0 80.35 6.289 117.6 18.297 49.57 15.703 90.02 52.481 111.06 99.551 14.02 31.469 20.87 66.27 20.87 103.051H4917c-1.52-31.117-5.8-62.133-12.83-91.098-22.83-94.863-89.32-174.371-177.68-211.621-100.54-42.242-210.54-66.699-326.72-66.699-89.92 0-176.48 14.219-257.73 39.668-123.97 39.199-231.31 128.398-273.93 249.98"/></g></svg>""")
        responses.add(
            method=responses.GET,
            url="https://lf-master-project-logos-prod.s3.us-east-2.amazonaws.com/open-timeline-io.svg",
            body="""<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="21.88 16.88 864.24 167.74"><title>Hitachi, Ltd. logo</title><g fill="#231f20" fill-opacity="1" fill-rule="nonzero" stroke="none" transform="matrix(1.33333 0 0 -1.33333 0 204.84) scale(.1)"><path d="M5301.18 1258.82V875.188h513.3c0-1.372-.43 383.632 0 383.632h254.16s.9-958.422 0-959.461h-254.16V721.57c0-1.25-513.3 0-513.3 0 .45-1.621 0-422.461 0-422.211h-254.12s1.6 959.461 0 959.461h254.12"/><path d="M2889.38 1258.82v-163.28h-388.51V299.359h-254.16v796.181h-388.48s.52 163.16 0 163.28c.52-.12 1031.15 0 1031.15 0"/><path d="M3877.23 299.359h-282.89c.42 0-83.32 206.289-83.32 206.289h-476.2s-81.72-206.519-83.17-206.289c.19-.23-282.82 0-282.82 0l448.28 959.461c0-.64 311.7 0 311.7 0zm-604.28 796.181l-176.76-436.216h353.76l-177 436.216"/><path d="M6269.85 299.359h254.3v959.461h-254.3V299.359"/><path d="M544.422 1258.82s-.137-386.449 0-383.632h512.968c0-1.372-.15 383.632 0 383.632h254.32s.63-958.422 0-959.461h-254.32V721.57c0-1.25-512.968 0-512.968 0 .109-1.621-.137-422.461 0-422.211H290.223s1.425 959.461 0 959.461h254.199"/><path d="M1513.27 299.359h253.93v959.461h-253.93V299.359"/><path d="M3868.11 565.32c-22.26 64.336-34.24 132.27-34.24 204.239 0 100.742 17.93 198.476 66.25 279.391 49.59 83.52 125.86 148.17 218.05 182.62 87.95 32.89 182.36 51.07 281.6 51.07 114.14 0 222.29-25.05 320.69-67.71 91.64-39.25 160.88-122.01 181.25-221.735 4.08-19.652 7.42-40.097 9.12-60.55h-266.68c-1.04 25.375-5.18 50.898-13.97 73.845-20.09 53.07-64.22 94.21-119.1 110.87-35.29 10.84-72.58 16.58-111.31 16.58-44.24 0-86.58-7.8-125.8-21.74-65.04-22.77-115.88-75.55-138.65-140.63-22.25-63.203-35-131.304-35-202.011 0-58.438 9.51-114.922 24.51-168.438 19.12-70.019 71.62-126.051 138.62-151.461 42.57-15.941 88.26-25.469 136.32-25.469 41.02 0 80.35 6.289 117.6 18.297 49.57 15.703 90.02 52.481 111.06 99.551 14.02 31.469 20.87 66.27 20.87 103.051H4917c-1.52-31.117-5.8-62.133-12.83-91.098-22.83-94.863-89.32-174.371-177.68-211.621-100.54-42.242-210.54-66.699-326.72-66.699-89.92 0-176.48 14.219-257.73 39.668-123.97 39.199-231.31 128.398-273.93 249.98"/></g></svg>""")
        responses.add(
            method=responses.GET,
            url="https://lf-master-project-logos-prod.s3.us-east-2.amazonaws.com/opencue.svg",
            body="""<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="21.88 16.88 864.24 167.74"><title>Hitachi, Ltd. logo</title><g fill="#231f20" fill-opacity="1" fill-rule="nonzero" stroke="none" transform="matrix(1.33333 0 0 -1.33333 0 204.84) scale(.1)"><path d="M5301.18 1258.82V875.188h513.3c0-1.372-.43 383.632 0 383.632h254.16s.9-958.422 0-959.461h-254.16V721.57c0-1.25-513.3 0-513.3 0 .45-1.621 0-422.461 0-422.211h-254.12s1.6 959.461 0 959.461h254.12"/><path d="M2889.38 1258.82v-163.28h-388.51V299.359h-254.16v796.181h-388.48s.52 163.16 0 163.28c.52-.12 1031.15 0 1031.15 0"/><path d="M3877.23 299.359h-282.89c.42 0-83.32 206.289-83.32 206.289h-476.2s-81.72-206.519-83.17-206.289c.19-.23-282.82 0-282.82 0l448.28 959.461c0-.64 311.7 0 311.7 0zm-604.28 796.181l-176.76-436.216h353.76l-177 436.216"/><path d="M6269.85 299.359h254.3v959.461h-254.3V299.359"/><path d="M544.422 1258.82s-.137-386.449 0-383.632h512.968c0-1.372-.15 383.632 0 383.632h254.32s.63-958.422 0-959.461h-254.32V721.57c0-1.25-512.968 0-512.968 0 .109-1.621-.137-422.461 0-422.211H290.223s1.425 959.461 0 959.461h254.199"/><path d="M1513.27 299.359h253.93v959.461h-253.93V299.359"/><path d="M3868.11 565.32c-22.26 64.336-34.24 132.27-34.24 204.239 0 100.742 17.93 198.476 66.25 279.391 49.59 83.52 125.86 148.17 218.05 182.62 87.95 32.89 182.36 51.07 281.6 51.07 114.14 0 222.29-25.05 320.69-67.71 91.64-39.25 160.88-122.01 181.25-221.735 4.08-19.652 7.42-40.097 9.12-60.55h-266.68c-1.04 25.375-5.18 50.898-13.97 73.845-20.09 53.07-64.22 94.21-119.1 110.87-35.29 10.84-72.58 16.58-111.31 16.58-44.24 0-86.58-7.8-125.8-21.74-65.04-22.77-115.88-75.55-138.65-140.63-22.25-63.203-35-131.304-35-202.011 0-58.438 9.51-114.922 24.51-168.438 19.12-70.019 71.62-126.051 138.62-151.461 42.57-15.941 88.26-25.469 136.32-25.469 41.02 0 80.35 6.289 117.6 18.297 49.57 15.703 90.02 52.481 111.06 99.551 14.02 31.469 20.87 66.27 20.87 103.051H4917c-1.52-31.117-5.8-62.133-12.83-91.098-22.83-94.863-89.32-174.371-177.68-211.621-100.54-42.242-210.54-66.699-326.72-66.699-89.92 0-176.48 14.219-257.73 39.668-123.97 39.199-231.31 128.398-273.93 249.98"/></g></svg>""")
        responses.add(
            method=responses.GET,
            url="https://api.github.com:443/orgs/OpenAssetIO",
            json={
                "login": "OpenAssetIO",
                "id": 105730218,
                "node_id": "O_kgDOBk1Qqg",
                "url": "https://api.github.com/orgs/OpenAssetIO",
                "repos_url": "https://api.github.com/orgs/OpenAssetIO/repos",
                "events_url": "https://api.github.com/orgs/OpenAssetIO/events",
                "hooks_url": "https://api.github.com/orgs/OpenAssetIO/hooks",
                "issues_url": "https://api.github.com/orgs/OpenAssetIO/issues",
                "members_url": "https://api.github.com/orgs/OpenAssetIO/members{/member}",
                "public_members_url": "https://api.github.com/orgs/OpenAssetIO/public_members{/member}",
                "avatar_url": "https://avatars.githubusercontent.com/u/105730218?v=4",
                "description": "An open-source interoperability standard for tools and content management systems used in media production.",
                "name": None,
                "company": None,
                "blog": None,
                "location": None,
                "email": None,
                "twitter_username": None,
                "is_verified": False,
                "has_organization_projects": True,
                "has_repository_projects": True,
                "public_repos": 11,
                "public_gists": 0,
                "followers": 44,
                "following": 0,
                "html_url": "https://github.com/OpenAssetIO",
                "created_at": "2022-05-17T14:16:16Z",
                "updated_at": "2022-05-17T15:29:44Z",
                "archived_at": None,
                "type": "Organization"
            })
        responses.add(
            method=responses.GET,
            url="https://api.github.com:443/orgs/academysoftwarefoundation",
            json={
                  "login": "AcademySoftwareFoundation",
                  "id": 40807682,
                  "node_id": "MDEyOk9yZ2FuaXphdGlvbjQwODA3Njgy",
                  "url": "https://api.github.com/orgs/AcademySoftwareFoundation",
                  "repos_url": "https://api.github.com/orgs/AcademySoftwareFoundation/repos",
                  "events_url": "https://api.github.com/orgs/AcademySoftwareFoundation/events",
                  "hooks_url": "https://api.github.com/orgs/AcademySoftwareFoundation/hooks",
                  "issues_url": "https://api.github.com/orgs/AcademySoftwareFoundation/issues",
                  "members_url": "https://api.github.com/orgs/AcademySoftwareFoundation/members{/member}",
                  "public_members_url": "https://api.github.com/orgs/AcademySoftwareFoundation/public_members{/member}",
                  "avatar_url": "https://avatars.githubusercontent.com/u/40807682?v=4",
                  "description": "Home for technical activities hosted by the Academy Software Foundation (ASWF).",
                  "name": "Academy Software Foundation",
                  "company": None,
                  "blog": "https://www.aswf.io/",
                  "location": None,
                  "email": "info@aswf.io",
                  "twitter_username": "AcademySwf",
                  "is_verified": False,
                  "has_organization_projects": True,
                  "has_repository_projects": True,
                  "public_repos": 44,
                  "public_gists": 0,
                  "followers": 968,
                  "following": 0,
                  "html_url": "https://github.com/AcademySoftwareFoundation",
                  "created_at": "2018-07-03T20:44:23Z",
                  "updated_at": "2024-07-01T13:19:22Z",
                  "archived_at": None,
                  "type": "Organization"
            })
        responses.add(
            method=responses.GET,
            url="https://api.github.com:443/orgs/AcademySoftwareFoundation/repos",
            json=[
                {
                    "id": 775131,
                    "node_id": "MDEwOlJlcG9zaXRvcnk3NzUxMzE=",
                    "name": "OpenColorIO",
                    "full_name": "AcademySoftwareFoundation/OpenColorIO",
                    "private": False,
                    "owner": {
                      "login": "AcademySoftwareFoundation",
                      "id": 40807682,
                      "node_id": "MDEyOk9yZ2FuaXphdGlvbjQwODA3Njgy",
                      "avatar_url": "https://avatars.githubusercontent.com/u/40807682?v=4",
                      "gravatar_id": "",
                      "url": "https://api.github.com/users/AcademySoftwareFoundation",
                      "html_url": "https://github.com/AcademySoftwareFoundation",
                      "followers_url": "https://api.github.com/users/AcademySoftwareFoundation/followers",
                      "following_url": "https://api.github.com/users/AcademySoftwareFoundation/following{/other_user}",
                      "gists_url": "https://api.github.com/users/AcademySoftwareFoundation/gists{/gist_id}",
                      "starred_url": "https://api.github.com/users/AcademySoftwareFoundation/starred{/owner}{/repo}",
                      "subscriptions_url": "https://api.github.com/users/AcademySoftwareFoundation/subscriptions",
                      "organizations_url": "https://api.github.com/users/AcademySoftwareFoundation/orgs",
                      "repos_url": "https://api.github.com/users/AcademySoftwareFoundation/repos",
                      "events_url": "https://api.github.com/users/AcademySoftwareFoundation/events{/privacy}",
                      "received_events_url": "https://api.github.com/users/AcademySoftwareFoundation/received_events",
                      "type": "Organization",
                      "site_admin": False
                    },
                    "html_url": "https://github.com/AcademySoftwareFoundation/OpenColorIO",
                    "description": "A color management framework for visual effects and animation.",
                    "fork": False,
                    "url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO",
                    "forks_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/forks",
                    "keys_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/keys{/key_id}",
                    "collaborators_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/collaborators{/collaborator}",
                    "teams_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/teams",
                    "hooks_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/hooks",
                    "issue_events_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/issues/events{/number}",
                    "events_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/events",
                    "assignees_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/assignees{/user}",
                    "branches_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/branches{/branch}",
                    "tags_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/tags",
                    "blobs_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/git/blobs{/sha}",
                    "git_tags_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/git/tags{/sha}",
                    "git_refs_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/git/refs{/sha}",
                    "trees_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/git/trees{/sha}",
                    "statuses_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/statuses/{sha}",
                    "languages_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/languages",
                    "stargazers_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/stargazers",
                    "contributors_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/contributors",
                    "subscribers_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/subscribers",
                    "subscription_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/subscription",
                    "commits_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/commits{/sha}",
                    "git_commits_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/git/commits{/sha}",
                    "comments_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/comments{/number}",
                    "issue_comment_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/issues/comments{/number}",
                    "contents_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/contents/{+path}",
                    "compare_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/compare/{base}...{head}",
                    "merges_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/merges",
                    "archive_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/{archive_format}{/ref}",
                    "downloads_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/downloads",
                    "issues_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/issues{/number}",
                    "pulls_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/pulls{/number}",
                    "milestones_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/milestones{/number}",
                    "notifications_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/notifications{?since,all,participating}",
                    "labels_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/labels{/name}",
                    "releases_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/releases{/id}",
                    "deployments_url": "https://api.github.com/repos/AcademySoftwareFoundation/OpenColorIO/deployments",
                    "created_at": "2010-07-14T18:22:06Z",
                    "updated_at": "2024-07-06T10:38:28Z",
                    "pushed_at": "2024-07-06T22:56:53Z",
                    "git_url": "git://github.com/AcademySoftwareFoundation/OpenColorIO.git",
                    "ssh_url": "git@github.com:AcademySoftwareFoundation/OpenColorIO.git",
                    "clone_url": "https://github.com/AcademySoftwareFoundation/OpenColorIO.git",
                    "svn_url": "https://github.com/AcademySoftwareFoundation/OpenColorIO",
                    "homepage": "https://opencolorio.org",
                    "size": 63041,
                    "stargazers_count": 1738,
                    "watchers_count": 1738,
                    "language": "C++",
                    "has_issues": True,
                    "has_projects": True,
                    "has_downloads": True,
                    "has_wiki": True,
                    "has_pages": True,
                    "has_discussions": False,
                    "forks_count": 430,
                    "mirror_url": None,
                    "archived": False,
                    "disabled": False,
                    "open_issues_count": 133,
                    "license": {
                      "key": "bsd-3-clause",
                      "name": "BSD 3-Clause \"New\" or \"Revised\" License",
                      "spdx_id": "BSD-3-Clause",
                      "url": "https://api.github.com/licenses/bsd-3-clause",
                      "node_id": "MDc6TGljZW5zZTU="
                    },
                    "allow_forking": True,
                    "is_template": False,
                    "web_commit_signoff_required": True,
                    "topics": [
                      "opencolorio"
                    ],
                    "visibility": "public",
                    "forks": 430,
                    "open_issues": 133,
                    "watchers": 1738,
                    "default_branch": "main",
                    "permissions": {
                      "admin": False,
                      "maintain": False,
                      "push": False,
                      "triage": False,
                      "pull": True
                    }
                }
            ])
        responses.add(
            method=responses.GET,
            url="https://api.github.com:443/orgs/OpenAssetIO/repos?per_page=1",
            json=[
                {
                    "id": 399068104,
                    "node_id": "MDEwOlJlcG9zaXRvcnkzOTkwNjgxMDQ=",
                    "name": "OpenAssetIO",
                    "full_name": "OpenAssetIO/OpenAssetIO",
                    "private": False,
                    "owner": {
                        "login": "OpenAssetIO",
                        "id": 105730218,
                        "node_id": "O_kgDOBk1Qqg",
                        "avatar_url": "https://avatars.githubusercontent.com/u/105730218?v=4",
                        "gravatar_id": "",
                        "url": "https://api.github.com/users/OpenAssetIO",
                        "html_url": "https://github.com/OpenAssetIO",
                        "followers_url": "https://api.github.com/users/OpenAssetIO/followers",
                        "following_url": "https://api.github.com/users/OpenAssetIO/following{/other_user}",
                        "gists_url": "https://api.github.com/users/OpenAssetIO/gists{/gist_id}",
                        "starred_url": "https://api.github.com/users/OpenAssetIO/starred{/owner}{/repo}",
                        "subscriptions_url": "https://api.github.com/users/OpenAssetIO/subscriptions",
                        "organizations_url": "https://api.github.com/users/OpenAssetIO/orgs",
                        "repos_url": "https://api.github.com/users/OpenAssetIO/repos",
                        "events_url": "https://api.github.com/users/OpenAssetIO/events{/privacy}",
                        "received_events_url": "https://api.github.com/users/OpenAssetIO/received_events",
                        "type": "Organization",
                        "site_admin": False
                    },
                    "html_url": "https://github.com/OpenAssetIO/OpenAssetIO",
                    "description": "An open-source interoperability standard for tools and content management systems used in media production.",
                    "fork": False,
                    "url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO",
                    "forks_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/forks",
                    "keys_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/keys{/key_id}",
                    "collaborators_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/collaborators{/collaborator}",
                    "teams_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/teams",
                    "hooks_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/hooks",
                    "issue_events_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/issues/events{/number}",
                    "events_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/events",
                    "assignees_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/assignees{/user}",
                    "branches_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/branches{/branch}",
                    "tags_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/tags",
                    "blobs_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/git/blobs{/sha}",
                    "git_tags_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/git/tags{/sha}",
                    "git_refs_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/git/refs{/sha}",
                    "trees_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/git/trees{/sha}",
                    "statuses_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/statuses/{sha}",
                    "languages_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/languages",
                    "stargazers_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/stargazers",
                    "contributors_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/contributors",
                    "subscribers_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/subscribers",
                    "subscription_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/subscription",
                    "commits_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/commits{/sha}",
                    "git_commits_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/git/commits{/sha}",
                    "comments_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/comments{/number}",
                    "issue_comment_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/issues/comments{/number}",
                    "contents_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/contents/{+path}",
                    "compare_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/compare/{base}...{head}",
                    "merges_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/merges",
                    "archive_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/{archive_format}{/ref}",
                    "downloads_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/downloads",
                    "issues_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/issues{/number}",
                    "pulls_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/pulls{/number}",
                    "milestones_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/milestones{/number}",
                    "notifications_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/notifications{?since,all,participating}",
                    "labels_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/labels{/name}",
                    "releases_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/releases{/id}",
                    "deployments_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/deployments",
                    "created_at": "2021-08-23T10:54:50Z",
                    "updated_at": "2024-06-07T11:32:08Z",
                    "pushed_at": "2024-06-10T15:36:44Z",
                    "git_url": "git://github.com/OpenAssetIO/OpenAssetIO.git",
                    "ssh_url": "git@github.com:OpenAssetIO/OpenAssetIO.git",
                    "clone_url": "https://github.com/OpenAssetIO/OpenAssetIO.git",
                    "svn_url": "https://github.com/OpenAssetIO/OpenAssetIO",
                    "homepage": "",
                    "size": 14943,
                    "stargazers_count": 268,
                    "watchers_count": 268,
                    "language": "C++",
                    "has_issues": True,
                    "has_projects": True,
                    "has_downloads": True,
                    "has_wiki": True,
                    "has_pages": True,
                    "has_discussions": True,
                    "forks_count": 28,
                    "mirror_url": None,
                    "archived": False,
                    "disabled": False,
                    "open_issues_count": 153,
                    "license": {
                        "key": "apache-2.0",
                        "name": "Apache License 2.0",
                        "spdx_id": "Apache-2.0",
                        "url": "https://api.github.com/licenses/apache-2.0",
                        "node_id": "MDc6TGljZW5zZTI="
                    },
                    "allow_forking": True,
                    "is_template": False,
                    "web_commit_signoff_required": True,
                    "topics": [
                        "asset-pipeline",
                        "assetmanager",
                        "cg",
                        "openassetio",
                        "vfx",
                        "vfx-pipeline"
                    ],
                    "visibility": "public",
                    "forks": 28,
                    "open_issues": 153,
                    "watchers": 268,
                    "default_branch": "main",
                    "permissions": {
                        "admin": False,
                        "maintain": False,
                        "push": False,
                        "triage": False,
                        "pull": True
                    }
                }
            ]
        )
        responses.add(
            method=responses.GET,
            url="https://api.github.com:443/orgs/OpenAssetIO/repos?per_page=1000",
            json=[
                {
                    "id": 399068104,
                    "node_id": "MDEwOlJlcG9zaXRvcnkzOTkwNjgxMDQ=",
                    "name": "OpenAssetIO",
                    "full_name": "OpenAssetIO/OpenAssetIO",
                    "private": False,
                    "owner": {
                        "login": "OpenAssetIO",
                        "id": 105730218,
                        "node_id": "O_kgDOBk1Qqg",
                        "avatar_url": "https://avatars.githubusercontent.com/u/105730218?v=4",
                        "gravatar_id": "",
                        "url": "https://api.github.com/users/OpenAssetIO",
                        "html_url": "https://github.com/OpenAssetIO",
                        "followers_url": "https://api.github.com/users/OpenAssetIO/followers",
                        "following_url": "https://api.github.com/users/OpenAssetIO/following{/other_user}",
                        "gists_url": "https://api.github.com/users/OpenAssetIO/gists{/gist_id}",
                        "starred_url": "https://api.github.com/users/OpenAssetIO/starred{/owner}{/repo}",
                        "subscriptions_url": "https://api.github.com/users/OpenAssetIO/subscriptions",
                        "organizations_url": "https://api.github.com/users/OpenAssetIO/orgs",
                        "repos_url": "https://api.github.com/users/OpenAssetIO/repos",
                        "events_url": "https://api.github.com/users/OpenAssetIO/events{/privacy}",
                        "received_events_url": "https://api.github.com/users/OpenAssetIO/received_events",
                        "type": "Organization",
                        "site_admin": False
                    },
                    "html_url": "https://github.com/OpenAssetIO/OpenAssetIO",
                    "description": "An open-source interoperability standard for tools and content management systems used in media production.",
                    "fork": False,
                    "url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO",
                    "forks_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/forks",
                    "keys_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/keys{/key_id}",
                    "collaborators_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/collaborators{/collaborator}",
                    "teams_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/teams",
                    "hooks_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/hooks",
                    "issue_events_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/issues/events{/number}",
                    "events_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/events",
                    "assignees_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/assignees{/user}",
                    "branches_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/branches{/branch}",
                    "tags_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/tags",
                    "blobs_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/git/blobs{/sha}",
                    "git_tags_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/git/tags{/sha}",
                    "git_refs_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/git/refs{/sha}",
                    "trees_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/git/trees{/sha}",
                    "statuses_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/statuses/{sha}",
                    "languages_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/languages",
                    "stargazers_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/stargazers",
                    "contributors_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/contributors",
                    "subscribers_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/subscribers",
                    "subscription_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/subscription",
                    "commits_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/commits{/sha}",
                    "git_commits_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/git/commits{/sha}",
                    "comments_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/comments{/number}",
                    "issue_comment_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/issues/comments{/number}",
                    "contents_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/contents/{+path}",
                    "compare_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/compare/{base}...{head}",
                    "merges_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/merges",
                    "archive_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/{archive_format}{/ref}",
                    "downloads_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/downloads",
                    "issues_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/issues{/number}",
                    "pulls_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/pulls{/number}",
                    "milestones_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/milestones{/number}",
                    "notifications_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/notifications{?since,all,participating}",
                    "labels_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/labels{/name}",
                    "releases_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/releases{/id}",
                    "deployments_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/deployments",
                    "created_at": "2021-08-23T10:54:50Z",
                    "updated_at": "2024-06-07T11:32:08Z",
                    "pushed_at": "2024-06-10T15:36:44Z",
                    "git_url": "git://github.com/OpenAssetIO/OpenAssetIO.git",
                    "ssh_url": "git@github.com:OpenAssetIO/OpenAssetIO.git",
                    "clone_url": "https://github.com/OpenAssetIO/OpenAssetIO.git",
                    "svn_url": "https://github.com/OpenAssetIO/OpenAssetIO",
                    "homepage": "",
                    "size": 14943,
                    "stargazers_count": 268,
                    "watchers_count": 268,
                    "language": "C++",
                    "has_issues": True,
                    "has_projects": True,
                    "has_downloads": True,
                    "has_wiki": True,
                    "has_pages": True,
                    "has_discussions": True,
                    "forks_count": 28,
                    "mirror_url": None,
                    "archived": False,
                    "disabled": False,
                    "open_issues_count": 153,
                    "license": {
                        "key": "apache-2.0",
                        "name": "Apache License 2.0",
                        "spdx_id": "Apache-2.0",
                        "url": "https://api.github.com/licenses/apache-2.0",
                        "node_id": "MDc6TGljZW5zZTI="
                    },
                    "allow_forking": True,
                    "is_template": False,
                    "web_commit_signoff_required": True,
                    "topics": [
                        "asset-pipeline",
                        "assetmanager",
                        "cg",
                        "openassetio",
                        "vfx",
                        "vfx-pipeline"
                    ],
                    "visibility": "public",
                    "forks": 28,
                    "open_issues": 153,
                    "watchers": 268,
                    "default_branch": "main",
                    "permissions": {
                        "admin": False,
                        "maintain": False,
                        "push": False,
                        "triage": False,
                        "pull": True
                    }
                }
            ]
        )
        responses.add(
            method=responses.GET,
            url="https://api-gw.platform.linuxfoundation.org/project-service/v1/public/projects?slug=aswf",
            json={
                  "Data": [
                    {
                      "AutoJoinEnabled": True,
                      "Description": "The mission of the Academy Software Foundation (ASWF) is to increase the quality and quantity of contributions to the content creation industry’s open source software base; to provide a neutral forum to coordinate cross-project efforts; to provide a common build and test infrastructure; and to provide individuals and organizations a clear path to participation in advancing our open source ecosystem.",
                      "DisplayOnWebsite": True,
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
                      "Website": "https://www.aswf.io/"
                    }
                  ],
                  "Metadata": {
                    "Offset": 0,
                    "PageSize": 100,
                    "TotalSize": 1
                  }
                }
            )
          
        with unittest.mock.patch('requests_cache.CachedSession', requests.Session):
            members.loadData()
        self.assertEqual(members.members[0].name,"OpenCue")
        self.assertEqual(members.members[0].crunchbase,"https://www.crunchbase.com/organization/linux-foundation")
        self.assertEqual(members.members[0].extra["facebook_url"],"https://www.facebook.com/TheLinuxFoundation")
        self.assertEqual(members.members[0].linkedin,"https://www.linkedin.com/company/208777")
        self.assertEqual(members.members[0].extra["reddit_url"],"https://www.reddit.com/r/vfx/")
        self.assertEqual(members.members[0].extra["pinterest_url"],"https://www.pinterest.com/linuxfoundation/")
        self.assertEqual(members.members[0].extra["youtube_url"],"https://www.youtube.com/user/TheLinuxFoundation")
        self.assertEqual(members.members[0].logo.filename(members.members[0].name),"opencue.svg")
        self.assertEqual(members.members[0].membership,"All")
        self.assertEqual(members.members[0].homepage_url,"https://opencue.io/")
        self.assertIsNone(members.members[0].twitter)
        self.assertIn("Project Group / Academy Software Foundation (ASWF)",members.members[0].second_path)
        self.assertEqual(members.members[1].name,"OpenTimelineIO")
        self.assertEqual(members.members[1].crunchbase,"https://www.crunchbase.com/organization/linux-foundation")
        self.assertEqual(members.members[1].logo.filename(members.members[1].name),"opentimelineio.svg")
        self.assertEqual(members.members[1].membership,"All")
        self.assertEqual(members.members[1].repo_url,"https://github.com/PixarAnimationStudios/OpenTimelineIO")
        self.assertEqual(members.members[1].homepage_url,"https://github.com/PixarAnimationStudios/OpenTimelineIO")
        self.assertIsNone(members.members[1].twitter)
        self.assertIn("PMO Managed / All", members.members[1].second_path)
        self.assertNotIn("Project Group / Academy Software Foundation (ASWF)",members.members[1].second_path)
        self.assertIsNone(members.members[2].homepage_url)
        self.assertIsNone(members.members[2].repo_url)
        self.assertEqual(members.members[2].logo.filename(members.members[2].name),"openexr.svg")
        self.assertEqual(members.members[3].repo_url,"https://github.com/OpenAssetIO/OpenAssetIO")
        self.assertIsNone(members.members[3].twitter)
        self.assertEqual(len(members.members),4)

    @responses.activate
    def testLoadDataSkippedRecords(self):
        config = Config()
        config.slug = 'aswf'
        config.projectsAddTechnologySector = True
        config.projectsAddIndustrySector = True
        config.projectsAddPMOManagedStatus = True
        config.projectsAddParentProject = True 
        members = LFXProjects(config=config,loadData=False)
        responses.add(
            method=responses.GET,
            url=members.endpointURL.format(members.project),
            json={
                "Data": [
                    {
                        "AutoJoinEnabled": False,
                        "Description": "OpenCue is an open source render management system. You can use OpenCue in visual effects and animation production to break down complex jobs into individual tasks. You can submit jobs to a configurable dispatch queue that allocates the necessary computational resources.",
                        "DisplayOnWebsite": False,
                        "HasProgramManager": False,
                        "Industry": [
                            "Motion Pictures"
                        ],
                        "IndustrySector": "Motion Pictures",
                        "Name": "OpenCue",
                        "ParentID": "a09410000182dD2AAI",
                        "ParentSlug": "aswf",
                        "ProjectID": "a092M00001IV3znQAD",
                        "ProjectLogo": "https://lf-master-project-logos-prod.s3.us-east-2.amazonaws.com/opencue.svg",
                        "ProjectType": "Project",
                        "RepositoryURL": "https://github.com/AcademySoftwareFoundation/OpenCue",
                        "Slug": "opencue",
                        "StartDate": "2020-04-24",
                        "Status": "Active",
                        "TechnologySector": "DevOps, CI/CD & Site Reliability;Web & Application Development;Visual Effects",
                        "TestRecord": False,
                        "Website": "https://opencue.io"
                    },
                    {
                        "AutoJoinEnabled": False,
                        "Description": "OpenCue is an open source render management system. You can use OpenCue in visual effects and animation production to break down complex jobs into individual tasks. You can submit jobs to a configurable dispatch queue that allocates the necessary computational resources.",
                        "DisplayOnWebsite": True,
                        "HasProgramManager": False,
                        "Industry": [
                            "Motion Pictures"
                        ],
                        "IndustrySector": "Motion Pictures",
                        "Name": "OpenCue",
                        "ParentID": "a09410000182dD2AAI",
                        "ParentSlug": "aswf",
                        "ProjectID": "a092M00001IV3znQAD",
                        "ProjectLogo": "https://lf-master-project-logos-prod.s3.us-east-2.amazonaws.com/opencue.svg",
                        "ProjectType": "Project",
                        "RepositoryURL": "https://github.com/AcademySoftwareFoundation/OpenCue",
                        "Slug": "opencue",
                        "StartDate": "2020-04-24",
                        "Status": "Formation - Exploratory",
                        "TechnologySector": "DevOps, CI/CD & Site Reliability;Web & Application Development;Visual Effects",
                        "TestRecord": False,
                        "Website": "https://opencue.io"
                    },
                    {
                        "AutoJoinEnabled": False,
                        "Description": "OpenTimelineIO (OTIO) is an API and interchange format for editorial cut information. You can think of it as a modern Edit Decision List (EDL) that also includes an API for reading, writing, and manipulating editorial data. It also includes a plugin system for translating to/from existing editorial formats as well as a plugin system for linking to proprietary media storage schemas.",
                        "DisplayOnWebsite": True,
                        "HasProgramManager": False,
                        "Industry": [
                            "Motion Pictures"
                        ],
                        "IndustrySector": "Motion Pictures",
                        "Name": "OpenTimelineIO",
                        "ParentID": "a09410000182dD2AAI",
                        "ParentSlug": "aswf",
                        "ProjectID": "a092M00001If9uZQAR",
                        "ProjectLogo": "https://lf-master-project-logos-prod.s3.us-east-2.amazonaws.com/open-timeline-io.svg",
                        "ProjectType": "Project",
                        "RepositoryURL": "https://github.com/PixarAnimationStudios/OpenTimelineIO",
                        "Slug": "open-timeline-io",
                        "StartDate": "2021-03-08",
                        "Status": "Active",
                        "TechnologySector": "Web & Application Development;Visual Effects",
                        "TestRecord": True,
                        "Website": "http://opentimeline.io/"
                    },
                ],
                "Metadata": {
                    "Offset": 0,
                    "PageSize": 100,
                    "TotalSize": 2
                }
            })
        
        with unittest.mock.patch('requests_cache.CachedSession', requests.Session):
            members.loadData()
        self.assertEqual(members.members,[])

if __name__ == '__main__':
    unittest.main()
