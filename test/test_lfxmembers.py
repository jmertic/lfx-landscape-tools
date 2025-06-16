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

class TestLFXMembers(unittest.TestCase):
    
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
            url="https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/hitachi-ltd.svg",
            body='<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="21.88 16.88 864.24 167.74"><title>Hitachi, Ltd. logo</title><g fill="#231f20" fill-opacity="1" fill-rule="nonzero" stroke="none" transform="matrix(1.33333 0 0 -1.33333 0 204.84) scale(.1)"><path d="M5301.18 1258.82V875.188h513.3c0-1.372-.43 383.632 0 383.632h254.16s.9-958.422 0-959.461h-254.16V721.57c0-1.25-513.3 0-513.3 0 .45-1.621 0-422.461 0-422.211h-254.12s1.6 959.461 0 959.461h254.12"/><path d="M2889.38 1258.82v-163.28h-388.51V299.359h-254.16v796.181h-388.48s.52 163.16 0 163.28c.52-.12 1031.15 0 1031.15 0"/><path d="M3877.23 299.359h-282.89c.42 0-83.32 206.289-83.32 206.289h-476.2s-81.72-206.519-83.17-206.289c.19-.23-282.82 0-282.82 0l448.28 959.461c0-.64 311.7 0 311.7 0zm-604.28 796.181l-176.76-436.216h353.76l-177 436.216"/><path d="M6269.85 299.359h254.3v959.461h-254.3V299.359"/><path d="M544.422 1258.82s-.137-386.449 0-383.632h512.968c0-1.372-.15 383.632 0 383.632h254.32s.63-958.422 0-959.461h-254.32V721.57c0-1.25-512.968 0-512.968 0 .109-1.621-.137-422.461 0-422.211H290.223s1.425 959.461 0 959.461h254.199"/><path d="M1513.27 299.359h253.93v959.461h-253.93V299.359"/><path d="M3868.11 565.32c-22.26 64.336-34.24 132.27-34.24 204.239 0 100.742 17.93 198.476 66.25 279.391 49.59 83.52 125.86 148.17 218.05 182.62 87.95 32.89 182.36 51.07 281.6 51.07 114.14 0 222.29-25.05 320.69-67.71 91.64-39.25 160.88-122.01 181.25-221.735 4.08-19.652 7.42-40.097 9.12-60.55h-266.68c-1.04 25.375-5.18 50.898-13.97 73.845-20.09 53.07-64.22 94.21-119.1 110.87-35.29 10.84-72.58 16.58-111.31 16.58-44.24 0-86.58-7.8-125.8-21.74-65.04-22.77-115.88-75.55-138.65-140.63-22.25-63.203-35-131.304-35-202.011 0-58.438 9.51-114.922 24.51-168.438 19.12-70.019 71.62-126.051 138.62-151.461 42.57-15.941 88.26-25.469 136.32-25.469 41.02 0 80.35 6.289 117.6 18.297 49.57 15.703 90.02 52.481 111.06 99.551 14.02 31.469 20.87 66.27 20.87 103.051H4917c-1.52-31.117-5.8-62.133-12.83-91.098-22.83-94.863-89.32-174.371-177.68-211.621-100.54-42.242-210.54-66.699-326.72-66.699-89.92 0-176.48 14.219-257.73 39.668-123.97 39.199-231.31 128.398-273.93 249.98"/></g></svg>')
        responses.add(
            method=responses.GET,
            url="https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/consensys_ag.svg",
            body='<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="21.88 16.88 864.24 167.74"><title>Hitachi, Ltd. logo</title><g fill="#231f20" fill-opacity="1" fill-rule="nonzero" stroke="none" transform="matrix(1.33333 0 0 -1.33333 0 204.84) scale(.1)"><path d="M5301.18 1258.82V875.188h513.3c0-1.372-.43 383.632 0 383.632h254.16s.9-958.422 0-959.461h-254.16V721.57c0-1.25-513.3 0-513.3 0 .45-1.621 0-422.461 0-422.211h-254.12s1.6 959.461 0 959.461h254.12"/><path d="M2889.38 1258.82v-163.28h-388.51V299.359h-254.16v796.181h-388.48s.52 163.16 0 163.28c.52-.12 1031.15 0 1031.15 0"/><path d="M3877.23 299.359h-282.89c.42 0-83.32 206.289-83.32 206.289h-476.2s-81.72-206.519-83.17-206.289c.19-.23-282.82 0-282.82 0l448.28 959.461c0-.64 311.7 0 311.7 0zm-604.28 796.181l-176.76-436.216h353.76l-177 436.216"/><path d="M6269.85 299.359h254.3v959.461h-254.3V299.359"/><path d="M544.422 1258.82s-.137-386.449 0-383.632h512.968c0-1.372-.15 383.632 0 383.632h254.32s.63-958.422 0-959.461h-254.32V721.57c0-1.25-512.968 0-512.968 0 .109-1.621-.137-422.461 0-422.211H290.223s1.425 959.461 0 959.461h254.199"/><path d="M1513.27 299.359h253.93v959.461h-253.93V299.359"/><path d="M3868.11 565.32c-22.26 64.336-34.24 132.27-34.24 204.239 0 100.742 17.93 198.476 66.25 279.391 49.59 83.52 125.86 148.17 218.05 182.62 87.95 32.89 182.36 51.07 281.6 51.07 114.14 0 222.29-25.05 320.69-67.71 91.64-39.25 160.88-122.01 181.25-221.735 4.08-19.652 7.42-40.097 9.12-60.55h-266.68c-1.04 25.375-5.18 50.898-13.97 73.845-20.09 53.07-64.22 94.21-119.1 110.87-35.29 10.84-72.58 16.58-111.31 16.58-44.24 0-86.58-7.8-125.8-21.74-65.04-22.77-115.88-75.55-138.65-140.63-22.25-63.203-35-131.304-35-202.011 0-58.438 9.51-114.922 24.51-168.438 19.12-70.019 71.62-126.051 138.62-151.461 42.57-15.941 88.26-25.469 136.32-25.469 41.02 0 80.35 6.289 117.6 18.297 49.57 15.703 90.02 52.481 111.06 99.551 14.02 31.469 20.87 66.27 20.87 103.051H4917c-1.52-31.117-5.8-62.133-12.83-91.098-22.83-94.863-89.32-174.371-177.68-211.621-100.54-42.242-210.54-66.699-326.72-66.699-89.92 0-176.48 14.219-257.73 39.668-123.97 39.199-231.31 128.398-273.93 249.98"/></g></svg>')
        responses.add(
            method=responses.GET,
            url=LFXMembers.endpointURLAllAutoJoinProjects,
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

    @responses.activate
    def testLoadData(self):
        responses.add(
            method=responses.GET,
            url=LFXMembers.endpointURL.format('tlf2'),
            body='[{"ID":"0014100000Te1TUAAZ","Name":"ConsenSys AG","CNCFLevel":"","OrganizationDescription":"this org is cool","LinkedInURL":"dog.com","CrunchBaseURL":"https://crunchbase.com/organization/consensus-systems--consensys-","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/consensys_ag.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":"","Website":"consensys.net"},{"ID":"0014100000Te04HAAR","Name":"Hitachi, Ltd.","CNCFLevel":"","LinkedInURL":"www.linkedin.com/company/hitachi-data-systems","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/hitachi-ltd.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":"https://yahoo.com","Website":"hitachi-systems.com"}]'
            )
        responses.add(
            method=responses.GET,
            url=LFXMembers.endpointURL.format('aswf'),
            body='[{"ID":"0014100000Te1TUAAZ","Name":"ConsenSys AG","CNCFLevel":"","OrganizationDescription":"this org is cool","LinkedInURL":"dog.com","CrunchBaseURL":"https://crunchbase.com/organization/consensus-systems--consensys-","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/consensys_ag.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","ProjectName":"Academy Software Foundation (ASWF)","Twitter":"","Website":"consensys.net"}]'
            )
        
        config = Config()
        config.project = 'tlf2'
        with unittest.mock.patch('requests_cache.CachedSession', requests.Session):
            members = LFXMembers(loadData = True, config=config)
        self.assertEqual(members.project,'tlf2')
        self.assertEqual(members.members[0].name,"ConsenSys AG")
        self.assertEqual(members.members[0].crunchbase,"https://www.crunchbase.com/organization/consensus-systems--consensys-")
        self.assertEqual(members.members[0].logo.filename(members.members[0].name),"consensys_ag.svg")
        self.assertEqual(members.members[0].membership,"Premier Membership")
        self.assertEqual(members.members[0].description,"this org is cool")
        self.assertEqual(members.members[0].homepage_url,"https://consensys.net/")
        self.assertNotIn('Project Membership / Academy Software Foundation (ASWF)',members.members[0].second_path)
        self.assertIsNone(members.members[0].linkedin)
        self.assertIsNone(members.members[0].twitter)
        self.assertEqual(members.members[1].name,"Hitachi, Ltd.")
        self.assertIsNone(members.members[1].crunchbase)
        self.assertEqual(members.members[1].logo.filename(members.members[1].name),"hitachi_ltd.svg")
        self.assertEqual(members.members[1].membership,"Premier Membership")
        self.assertEqual(members.members[1].homepage_url,"https://hitachi-systems.com/")
        self.assertIsNone(members.members[1].twitter)
        self.assertNotIn('Project Membership / Academy Software Foundation (ASWF)',members.members[1].second_path)
    
    @responses.activate
    def testLoadData(self):
        responses.add(
            method=responses.GET,
            url=LFXMembers.endpointURL.format('tlf2'),
            body='[{"ID":"0014100000Te1TUAAZ","Name":"ConsenSys AG","CNCFLevel":"","OrganizationDescription":"this org is cool","LinkedInURL":"dog.com","CrunchBaseURL":"https://crunchbase.com/organization/consensus-systems--consensys-","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/consensys_ag.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":"","Website":"consensys.net"},{"ID":"0014100000Te04HAAR","Name":"Hitachi, Ltd.","CNCFLevel":"","LinkedInURL":"www.linkedin.com/company/hitachi-data-systems","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/hitachi-ltd.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":"https://yahoo.com","Website":"hitachi-systems.com"}]'
            )
        responses.add(
            method=responses.GET,
            url=LFXMembers.endpointURL.format('aswf'),
            body='[{"ID":"0014100000Te1TUAAZ","Name":"ConsenSys AG","CNCFLevel":"","OrganizationDescription":"this org is cool","LinkedInURL":"dog.com","CrunchBaseURL":"https://crunchbase.com/organization/consensus-systems--consensys-","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/consensys_ag.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","ProjectName":"Academy Software Foundation (ASWF)","Twitter":"","Website":"consensys.net"}]'
            )
        
        config = Config()
        config.project = 'tlf2'
        config.addOtherProjectMemberships = True
        with unittest.mock.patch('requests_cache.CachedSession', requests.Session):
            members = LFXMembers(loadData = True, config=config)
        self.assertEqual(members.project,'tlf2')
        self.assertEqual(members.members[0].name,"ConsenSys AG")
        self.assertEqual(members.members[0].crunchbase,"https://www.crunchbase.com/organization/consensus-systems--consensys-")
        self.assertEqual(members.members[0].logo.filename(members.members[0].name),"consensys_ag.svg")
        self.assertEqual(members.members[0].membership,"Premier Membership")
        self.assertEqual(members.members[0].description,"this org is cool")
        self.assertEqual(members.members[0].homepage_url,"https://consensys.net/")
        self.assertIn('Project Membership / Academy Software Foundation (ASWF)',members.members[0].second_path)
        self.assertIsNone(members.members[0].linkedin)
        self.assertIsNone(members.members[0].twitter)
        self.assertEqual(members.members[1].name,"Hitachi, Ltd.")
        self.assertIsNone(members.members[1].crunchbase)
        self.assertEqual(members.members[1].logo.filename(members.members[1].name),"hitachi_ltd.svg")
        self.assertEqual(members.members[1].membership,"Premier Membership")
        self.assertEqual(members.members[1].homepage_url,"https://hitachi-systems.com/")
        self.assertIsNone(members.members[1].twitter)
        self.assertNotIn('Project Membership / Academy Software Foundation (ASWF)',members.members[1].second_path)
    
    @responses.activate
    def testLoadDataMissingLogo(self):
        config = Config()
        config.project = 'tlf'
        members = LFXMembers(config=config,loadData = False)
        responses.add(
            method=responses.GET,
            url=members.endpointURL.format(members.project),
            body="""[{"ID":"0014100000Te1TUAAZ","Name":"ConsenSys AG","CNCFLevel":"","CrunchBaseURL":"https://crunchbase.com/organization/consensus-systems--consensys-","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":""},{"ID":"0014100000Te04HAAR","Name":"Hitachi, Ltd.","CNCFLevel":"","LinkedInURL":"www.linkedin.com/company/hitachi-data-systems","Logo":"","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":"","Website":"hitachi-systems.com"}]"""
            )

        with unittest.mock.patch('requests_cache.CachedSession', requests.Session):
            members.loadData()
        self.assertEqual(members.project,'tlf')
        self.assertEqual(members.members[0].name,"ConsenSys AG")
        self.assertEqual(members.members[0].crunchbase,"https://www.crunchbase.com/organization/consensus-systems--consensys-")
        self.assertEqual(members.members[0].logo.filename(members.members[0].name),"consensys_ag.svg")
        self.assertEqual(members.members[0].membership,"Premier Membership")
        self.assertIsNone(members.members[0].homepage_url)
        self.assertIsNone(members.members[0].twitter)
        self.assertEqual(members.members[1].name,"Hitachi, Ltd.")
        self.assertIsNone(members.members[1].crunchbase)
        self.assertEqual(members.members[1].logo.filename(members.members[1].name),"hitachi_ltd.svg")
        self.assertEqual(members.members[1].membership,"Premier Membership")
        self.assertEqual(members.members[1].homepage_url,"https://hitachi-systems.com/")
        self.assertIsNone(members.members[1].twitter)
        self.assertEqual(members.members[1].linkedin,"https://www.linkedin.com/company/hitachi-data-systems")

    @responses.activate
    def testLoadDataMissinghomepage_url(self):
        config = Config()
        config.project = 'tlf'
        members = LFXMembers(config=config,loadData = False)
        responses.add(
            method=responses.GET,
            url=members.endpointURL.format(members.project),
            body="""[{"ID":"0014100000Te1TUAAZ","Name":"ConsenSys AG","CNCFLevel":"","CrunchBaseURL":"https://crunchbase.com/organization/consensus-systems--consensys-","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/consensys_ag.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":""},{"ID":"0014100000Te04HAAR","Name":"Hitachi, Ltd.","CNCFLevel":"","LinkedInURL":"www.linkedin.com/company/hitachi-data-systems","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/hitachi-ltd.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":"","Website":"hitachi-systems.com"}]"""
            )

        with unittest.mock.patch('requests_cache.CachedSession', requests.Session):
            members.loadData()
        self.assertEqual(members.project,'tlf')
        self.assertEqual(members.members[0].name,"ConsenSys AG")
        self.assertEqual(members.members[0].crunchbase,"https://www.crunchbase.com/organization/consensus-systems--consensys-")
        self.assertEqual(members.members[0].logo.filename(members.members[0].name),"consensys_ag.svg")
        self.assertEqual(members.members[0].membership,"Premier Membership")
        self.assertIsNone(members.members[0].homepage_url)
        self.assertIsNone(members.members[0].twitter)
        self.assertEqual(members.members[1].name,"Hitachi, Ltd.")
        self.assertIsNone(members.members[1].crunchbase)
        self.assertEqual(members.members[1].logo.filename(members.members[1].name),"hitachi_ltd.svg")
        self.assertEqual(members.members[1].membership,"Premier Membership")
        self.assertEqual(members.members[1].homepage_url,"https://hitachi-systems.com/")
        self.assertIsNone(members.members[1].twitter)

    @responses.activate
    def testLoadDataDuplicates(self):
        config = Config()
        config.project = 'tlf'
        members = LFXMembers(config=config,loadData = False)
        responses.add(
            url=members.endpointURL.format(members.project),
            method=responses.GET,
            body="""[{"ID":"0014100000Te1TUAAZ","Name":"ConsenSys AG","CNCFLevel":"","CrunchBaseURL":"https://crunchbase.com/organization/consensus-systems--consensys-","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/consensys_ag.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":"","homepage_url":"consensys.net"},{"ID":"0014100000Te1TUAAZ","Name":"ConsenSys AG","CNCFLevel":"","CrunchBaseURL":"https://crunchbase.com/organization/consensus-systems--consensys-","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/consensys_ag.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":"","homepage_url":"consensys.net"},{"ID":"0014100000Te04HAAR","Name":"Hitachi, Ltd.","CNCFLevel":"","LinkedInURL":"www.linkedin.com/company/hitachi-data-systems","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/hitachi-ltd.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":"","Website":"hitachi-systems.com"}]"""
            )

        with unittest.mock.patch('requests_cache.CachedSession', requests.Session):
            members.loadData()
        self.assertEqual(members.project,'tlf')
        self.assertEqual(len(members.members),2)

if __name__ == '__main__':
    unittest.main()
