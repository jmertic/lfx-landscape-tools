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

class TestLandscapeMembers(unittest.TestCase):

    @responses.activate
    def testLoadData(self):
        members = LandscapeMembers(loadData = False)
        responses.add(
            method=responses.GET,
            url=members.landscapeListYAML,
            body="""
landscapes:
  # name: how we name a landscape project, used on a build server for logs and settings
  # repo: a github repo for a specific landscape
  # netlify: full | skip - do we build it on a netlify build or not
  # hook: - id for a build hook, so it will be triggered after a master build
  - landscape:
    name: aswf
    repo: AcademySoftwareFoundation/aswf-landscape
    hook: 5d5c7ca6dc2c51cf02381f63
    required: true
"""
            )
        responses.add(
            method=responses.GET,
            url=members.landscapeSettingsYAML.format(repo="AcademySoftwareFoundation/aswf-landscape"),
            body="""
global:
  membership: ASWF Members
"""
            )
        responses.add(
            method=responses.GET,
            url=members.landscapeLandscapeYAML.format(repo="AcademySoftwareFoundation/aswf-landscape"),
            body="""
landscape:
  - category:
    name: ASWF Members
    subcategories:
      - subcategory:
        name: Premier
        items:
          - item:
            name: Academy of Motion Picture Arts and Sciences
            homepage_url: https://oscars.org/
            logo: academy_of_motion_picture_arts_and_sciences.svg
            twitter: https://twitter.com/TheAcademy
            enduser: true
            crunchbase: https://www.crunchbase.com/organization/the-academy-of-motion-picture-arts-and-sciences
      - subcategory:
        name: Associate
        items:
          - item:
            name: Blender Foundation
            homepage_url: https://blender.org/
            logo: blender_foundation.svg
            twitter: https://twitter.com/Blender_Cloud
            crunchbase: https://www.crunchbase.com/organization/blender-org
"""
                )
        responses.add(
            method=responses.GET,
            url="https://raw.githubusercontent.com/AcademySoftwareFoundation/aswf-landscape/master/hosted_logos/academy_of_motion_picture_arts_and_sciences.svg",
            body="""<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="21.88 16.88 864.24 167.74"><title>Hitachi, Ltd. logo</title><g fill="#231f20" fill-opacity="1" fill-rule="nonzero" stroke="none" transform="matrix(1.33333 0 0 -1.33333 0 204.84) scale(.1)"><path d="M5301.18 1258.82V875.188h513.3c0-1.372-.43 383.632 0 383.632h254.16s.9-958.422 0-959.461h-254.16V721.57c0-1.25-513.3 0-513.3 0 .45-1.621 0-422.461 0-422.211h-254.12s1.6 959.461 0 959.461h254.12"/><path d="M2889.38 1258.82v-163.28h-388.51V299.359h-254.16v796.181h-388.48s.52 163.16 0 163.28c.52-.12 1031.15 0 1031.15 0"/><path d="M3877.23 299.359h-282.89c.42 0-83.32 206.289-83.32 206.289h-476.2s-81.72-206.519-83.17-206.289c.19-.23-282.82 0-282.82 0l448.28 959.461c0-.64 311.7 0 311.7 0zm-604.28 796.181l-176.76-436.216h353.76l-177 436.216"/><path d="M6269.85 299.359h254.3v959.461h-254.3V299.359"/><path d="M544.422 1258.82s-.137-386.449 0-383.632h512.968c0-1.372-.15 383.632 0 383.632h254.32s.63-958.422 0-959.461h-254.32V721.57c0-1.25-512.968 0-512.968 0 .109-1.621-.137-422.461 0-422.211H290.223s1.425 959.461 0 959.461h254.199"/><path d="M1513.27 299.359h253.93v959.461h-253.93V299.359"/><path d="M3868.11 565.32c-22.26 64.336-34.24 132.27-34.24 204.239 0 100.742 17.93 198.476 66.25 279.391 49.59 83.52 125.86 148.17 218.05 182.62 87.95 32.89 182.36 51.07 281.6 51.07 114.14 0 222.29-25.05 320.69-67.71 91.64-39.25 160.88-122.01 181.25-221.735 4.08-19.652 7.42-40.097 9.12-60.55h-266.68c-1.04 25.375-5.18 50.898-13.97 73.845-20.09 53.07-64.22 94.21-119.1 110.87-35.29 10.84-72.58 16.58-111.31 16.58-44.24 0-86.58-7.8-125.8-21.74-65.04-22.77-115.88-75.55-138.65-140.63-22.25-63.203-35-131.304-35-202.011 0-58.438 9.51-114.922 24.51-168.438 19.12-70.019 71.62-126.051 138.62-151.461 42.57-15.941 88.26-25.469 136.32-25.469 41.02 0 80.35 6.289 117.6 18.297 49.57 15.703 90.02 52.481 111.06 99.551 14.02 31.469 20.87 66.27 20.87 103.051H4917c-1.52-31.117-5.8-62.133-12.83-91.098-22.83-94.863-89.32-174.371-177.68-211.621-100.54-42.242-210.54-66.699-326.72-66.699-89.92 0-176.48 14.219-257.73 39.668-123.97 39.199-231.31 128.398-273.93 249.98"/></g></svg>""")
        responses.add(
            method=responses.GET,
            url="https://raw.githubusercontent.com/AcademySoftwareFoundation/aswf-landscape/master/hosted_logos/blender_foundation.svg",
            body="""<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="21.88 16.88 864.24 167.74"><title>Hitachi, Ltd. logo</title><g fill="#231f20" fill-opacity="1" fill-rule="nonzero" stroke="none" transform="matrix(1.33333 0 0 -1.33333 0 204.84) scale(.1)"><path d="M5301.18 1258.82V875.188h513.3c0-1.372-.43 383.632 0 383.632h254.16s.9-958.422 0-959.461h-254.16V721.57c0-1.25-513.3 0-513.3 0 .45-1.621 0-422.461 0-422.211h-254.12s1.6 959.461 0 959.461h254.12"/><path d="M2889.38 1258.82v-163.28h-388.51V299.359h-254.16v796.181h-388.48s.52 163.16 0 163.28c.52-.12 1031.15 0 1031.15 0"/><path d="M3877.23 299.359h-282.89c.42 0-83.32 206.289-83.32 206.289h-476.2s-81.72-206.519-83.17-206.289c.19-.23-282.82 0-282.82 0l448.28 959.461c0-.64 311.7 0 311.7 0zm-604.28 796.181l-176.76-436.216h353.76l-177 436.216"/><path d="M6269.85 299.359h254.3v959.461h-254.3V299.359"/><path d="M544.422 1258.82s-.137-386.449 0-383.632h512.968c0-1.372-.15 383.632 0 383.632h254.32s.63-958.422 0-959.461h-254.32V721.57c0-1.25-512.968 0-512.968 0 .109-1.621-.137-422.461 0-422.211H290.223s1.425 959.461 0 959.461h254.199"/><path d="M1513.27 299.359h253.93v959.461h-253.93V299.359"/><path d="M3868.11 565.32c-22.26 64.336-34.24 132.27-34.24 204.239 0 100.742 17.93 198.476 66.25 279.391 49.59 83.52 125.86 148.17 218.05 182.62 87.95 32.89 182.36 51.07 281.6 51.07 114.14 0 222.29-25.05 320.69-67.71 91.64-39.25 160.88-122.01 181.25-221.735 4.08-19.652 7.42-40.097 9.12-60.55h-266.68c-1.04 25.375-5.18 50.898-13.97 73.845-20.09 53.07-64.22 94.21-119.1 110.87-35.29 10.84-72.58 16.58-111.31 16.58-44.24 0-86.58-7.8-125.8-21.74-65.04-22.77-115.88-75.55-138.65-140.63-22.25-63.203-35-131.304-35-202.011 0-58.438 9.51-114.922 24.51-168.438 19.12-70.019 71.62-126.051 138.62-151.461 42.57-15.941 88.26-25.469 136.32-25.469 41.02 0 80.35 6.289 117.6 18.297 49.57 15.703 90.02 52.481 111.06 99.551 14.02 31.469 20.87 66.27 20.87 103.051H4917c-1.52-31.117-5.8-62.133-12.83-91.098-22.83-94.863-89.32-174.371-177.68-211.621-100.54-42.242-210.54-66.699-326.72-66.699-89.92 0-176.48 14.219-257.73 39.668-123.97 39.199-231.31 128.398-273.93 249.98"/></g></svg>""")
        

        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            members.loadData()
        self.assertEqual(members.members[0].orgname,"Academy of Motion Picture Arts and Sciences")
        self.assertEqual(members.members[1].orgname,"Blender Foundation")
    
    @responses.activate
    def testLoadDataSpecifyLandscapeYAML(self):
        members = LandscapeMembers(loadData = False, landscapeListYAML = 'https://dog.com')
        responses.add(
            method=responses.GET,
            url=members.landscapeListYAML,
            body="""
landscapes:
  # name: how we name a landscape project, used on a build server for logs and settings
  # repo: a github repo for a specific landscape
  # netlify: full | skip - do we build it on a netlify build or not
  # hook: - id for a build hook, so it will be triggered after a master build
  - landscape:
    name: aswf
    repo: AcademySoftwareFoundation/aswf-landscape
    hook: 5d5c7ca6dc2c51cf02381f63
    required: true
"""
            )
        responses.add(
            method=responses.GET,
            url=members.landscapeSettingsYAML.format(repo="AcademySoftwareFoundation/aswf-landscape"),
            body="""
global:
  membership: ASWF Members
"""
            )
        responses.add(
            method=responses.GET,
            url=members.landscapeLandscapeYAML.format(repo="AcademySoftwareFoundation/aswf-landscape"),
            body="""
landscape:
  - category:
    name: ASWF Members
    subcategories:
      - subcategory:
        name: Premier
        items:
          - item:
            name: Academy of Motion Picture Arts and Sciences
            homepage_url: https://oscars.org/
            logo: academy_of_motion_picture_arts_and_sciences.svg
            twitter: https://twitter.com/TheAcademy
            crunchbase: https://www.crunchbase.com/organization/the-academy-of-motion-picture-arts-and-sciences
      - subcategory:
        name: Associate
        items:
          - item:
            name: Blender Foundation
            homepage_url: https://blender.org/
            logo: blender_foundation.svg
            twitter: https://twitter.com/Blender_Cloud
            crunchbase: https://www.crunchbase.com/organization/blender-org
"""
                )
        responses.add(
            method=responses.GET,
            url="https://raw.githubusercontent.com/AcademySoftwareFoundation/aswf-landscape/master/hosted_logos/academy_of_motion_picture_arts_and_sciences.svg",
            body="""<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="21.88 16.88 864.24 167.74"><title>Hitachi, Ltd. logo</title><g fill="#231f20" fill-opacity="1" fill-rule="nonzero" stroke="none" transform="matrix(1.33333 0 0 -1.33333 0 204.84) scale(.1)"><path d="M5301.18 1258.82V875.188h513.3c0-1.372-.43 383.632 0 383.632h254.16s.9-958.422 0-959.461h-254.16V721.57c0-1.25-513.3 0-513.3 0 .45-1.621 0-422.461 0-422.211h-254.12s1.6 959.461 0 959.461h254.12"/><path d="M2889.38 1258.82v-163.28h-388.51V299.359h-254.16v796.181h-388.48s.52 163.16 0 163.28c.52-.12 1031.15 0 1031.15 0"/><path d="M3877.23 299.359h-282.89c.42 0-83.32 206.289-83.32 206.289h-476.2s-81.72-206.519-83.17-206.289c.19-.23-282.82 0-282.82 0l448.28 959.461c0-.64 311.7 0 311.7 0zm-604.28 796.181l-176.76-436.216h353.76l-177 436.216"/><path d="M6269.85 299.359h254.3v959.461h-254.3V299.359"/><path d="M544.422 1258.82s-.137-386.449 0-383.632h512.968c0-1.372-.15 383.632 0 383.632h254.32s.63-958.422 0-959.461h-254.32V721.57c0-1.25-512.968 0-512.968 0 .109-1.621-.137-422.461 0-422.211H290.223s1.425 959.461 0 959.461h254.199"/><path d="M1513.27 299.359h253.93v959.461h-253.93V299.359"/><path d="M3868.11 565.32c-22.26 64.336-34.24 132.27-34.24 204.239 0 100.742 17.93 198.476 66.25 279.391 49.59 83.52 125.86 148.17 218.05 182.62 87.95 32.89 182.36 51.07 281.6 51.07 114.14 0 222.29-25.05 320.69-67.71 91.64-39.25 160.88-122.01 181.25-221.735 4.08-19.652 7.42-40.097 9.12-60.55h-266.68c-1.04 25.375-5.18 50.898-13.97 73.845-20.09 53.07-64.22 94.21-119.1 110.87-35.29 10.84-72.58 16.58-111.31 16.58-44.24 0-86.58-7.8-125.8-21.74-65.04-22.77-115.88-75.55-138.65-140.63-22.25-63.203-35-131.304-35-202.011 0-58.438 9.51-114.922 24.51-168.438 19.12-70.019 71.62-126.051 138.62-151.461 42.57-15.941 88.26-25.469 136.32-25.469 41.02 0 80.35 6.289 117.6 18.297 49.57 15.703 90.02 52.481 111.06 99.551 14.02 31.469 20.87 66.27 20.87 103.051H4917c-1.52-31.117-5.8-62.133-12.83-91.098-22.83-94.863-89.32-174.371-177.68-211.621-100.54-42.242-210.54-66.699-326.72-66.699-89.92 0-176.48 14.219-257.73 39.668-123.97 39.199-231.31 128.398-273.93 249.98"/></g></svg>""")
        responses.add(
            method=responses.GET,
            url="https://raw.githubusercontent.com/AcademySoftwareFoundation/aswf-landscape/master/hosted_logos/blender_foundation.svg",
            body="""<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="21.88 16.88 864.24 167.74"><title>Hitachi, Ltd. logo</title><g fill="#231f20" fill-opacity="1" fill-rule="nonzero" stroke="none" transform="matrix(1.33333 0 0 -1.33333 0 204.84) scale(.1)"><path d="M5301.18 1258.82V875.188h513.3c0-1.372-.43 383.632 0 383.632h254.16s.9-958.422 0-959.461h-254.16V721.57c0-1.25-513.3 0-513.3 0 .45-1.621 0-422.461 0-422.211h-254.12s1.6 959.461 0 959.461h254.12"/><path d="M2889.38 1258.82v-163.28h-388.51V299.359h-254.16v796.181h-388.48s.52 163.16 0 163.28c.52-.12 1031.15 0 1031.15 0"/><path d="M3877.23 299.359h-282.89c.42 0-83.32 206.289-83.32 206.289h-476.2s-81.72-206.519-83.17-206.289c.19-.23-282.82 0-282.82 0l448.28 959.461c0-.64 311.7 0 311.7 0zm-604.28 796.181l-176.76-436.216h353.76l-177 436.216"/><path d="M6269.85 299.359h254.3v959.461h-254.3V299.359"/><path d="M544.422 1258.82s-.137-386.449 0-383.632h512.968c0-1.372-.15 383.632 0 383.632h254.32s.63-958.422 0-959.461h-254.32V721.57c0-1.25-512.968 0-512.968 0 .109-1.621-.137-422.461 0-422.211H290.223s1.425 959.461 0 959.461h254.199"/><path d="M1513.27 299.359h253.93v959.461h-253.93V299.359"/><path d="M3868.11 565.32c-22.26 64.336-34.24 132.27-34.24 204.239 0 100.742 17.93 198.476 66.25 279.391 49.59 83.52 125.86 148.17 218.05 182.62 87.95 32.89 182.36 51.07 281.6 51.07 114.14 0 222.29-25.05 320.69-67.71 91.64-39.25 160.88-122.01 181.25-221.735 4.08-19.652 7.42-40.097 9.12-60.55h-266.68c-1.04 25.375-5.18 50.898-13.97 73.845-20.09 53.07-64.22 94.21-119.1 110.87-35.29 10.84-72.58 16.58-111.31 16.58-44.24 0-86.58-7.8-125.8-21.74-65.04-22.77-115.88-75.55-138.65-140.63-22.25-63.203-35-131.304-35-202.011 0-58.438 9.51-114.922 24.51-168.438 19.12-70.019 71.62-126.051 138.62-151.461 42.57-15.941 88.26-25.469 136.32-25.469 41.02 0 80.35 6.289 117.6 18.297 49.57 15.703 90.02 52.481 111.06 99.551 14.02 31.469 20.87 66.27 20.87 103.051H4917c-1.52-31.117-5.8-62.133-12.83-91.098-22.83-94.863-89.32-174.371-177.68-211.621-100.54-42.242-210.54-66.699-326.72-66.699-89.92 0-176.48 14.219-257.73 39.668-123.97 39.199-231.31 128.398-273.93 249.98"/></g></svg>""")
        

        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            members.loadData()
        self.assertEqual(members.members[0].orgname,"Academy of Motion Picture Arts and Sciences")
        self.assertEqual(members.members[1].orgname,"Blender Foundation")
    
    @responses.activate
    def testLoadDataSkipLandscape(self):
        members = LandscapeMembers(loadData = False)
        members.skipLandscapes = ['aswf']
        responses.add(
            method=responses.GET,
            url=members.landscapeListYAML,
            body="""
landscapes:
  # name: how we name a landscape project, used on a build server for logs and settings
  # repo: a github repo for a specific landscape
  # netlify: full | skip - do we build it on a netlify build or not
  # hook: - id for a build hook, so it will be triggered after a master build
  - landscape:
    name: aswf
    repo: AcademySoftwareFoundation/aswf-landscape
    hook: 5d5c7ca6dc2c51cf02381f63
    required: true
"""
            )
        responses.add(
            method=responses.GET,
            url=members.landscapeSettingsYAML.format(repo="AcademySoftwareFoundation/aswf-landscape"),
            body="""
global:
  membership: ASWF Members
"""
            )
        responses.add(
            method=responses.GET,
            url=members.landscapeLandscapeYAML.format(repo="AcademySoftwareFoundation/aswf-landscape"),
            body="""
landscape:
  - category:
    name: ASWF Members
    subcategories:
      - subcategory:
        name: Premier
        items:
          - item:
            name: Academy of Motion Picture Arts and Sciences
            homepage_url: https://oscars.org/
            logo: academy_of_motion_picture_arts_and_sciences.svg
            twitter: https://twitter.com/TheAcademy
            crunchbase: https://www.crunchbase.com/organization/the-academy-of-motion-picture-arts-and-sciences
      - subcategory:
        name: Associate
        items:
          - item:
            name: Blender Foundation
            homepage_url: https://blender.org/
            logo: blender_foundation.svg
            twitter: https://twitter.com/Blender_Cloud
            crunchbase: https://www.crunchbase.com/organization/blender-org
"""
                )
        members.loadData()
        self.assertEqual(members.members,[])

    @responses.activate
    def testLoadDataInvalidYAML(self):
        members = LandscapeMembers(loadData = False)
        responses.add(
            method=responses.GET,
            url=members.landscapeListYAML,
            body="""
landscapes:
  # name: how we name a landscape project, used on a build server for logs and settings
  # repo: a github repo for a specific landscape
  # netlify: full | skip - do we build it on a netlify build or not
  # hook: - id for a build hook, so it will be triggered after a master build
  - landscape:
    name: aswf
    repo: AcademySoftwareFoundation/aswf-landscape
    hook: 5d5c7ca6dc2c51cf02381f63
    required: true
"""
            )
        responses.add(
            method=responses.GET,
            url=members.landscapeSettingsYAML.format(repo="AcademySoftwareFoundation/aswf-landscape"),
            body="""
global:
  membership: ASWF Members
"""
            )
        responses.add(
            method=responses.GET,
            url=members.landscapeLandscapeYAML.format(repo="AcademySoftwareFoundation/aswf-landscape"),
            body="""
landscape:
  - category:
    name: ASWF Members
    subcategories:
      - subcategory:
        name: Premier
        items:
          - item:
            name: Academy of Motion Picture Arts and Sciences
            homepage_url: https://aswf.io
            homepage_url: https://oscars.org/
            logo: academy_of_motion_picture_arts_and_sciences.svg
            twitter: https://twitter.com/TheAcademy
            crunchbase: https://www.crunchbase.com/organization/the-academy-of-motion-picture-arts-and-sciences
      - subcategory:
        name: Associate
        items:
          - item:
            name: Blender Foundation
            homepage_url: https://blender.org/
            logo: blender_foundation.svg
            twitter: https://twitter.com/Blender_Cloud
            crunchbase: https://www.crunchbase.com/organization/blender-org
"""
                )
        self.assertRaises(Exception,members.loadData())
    
    @responses.activate
    def testLoadDataBadLandscape(self):
        members = LandscapeMembers(loadData = False)
        responses.add(
            method=responses.GET,
            url=members.landscapeListYAML,
            body="""
landscapes:
  # name: how we name a landscape project, used on a build server for logs and settings
  # repo: a github repo for a specific landscape
  # netlify: full | skip - do we build it on a netlify build or not
  # hook: - id for a build hook, so it will be triggered after a master build
  - landscape:
    name: aswf
    repo: AcademySoftwareFoundation/aswf-landscape
    hook: 5d5c7ca6dc2c51cf02381f63
    required: true
"""
            )
        responses.add(
            method=responses.GET,
            url=members.landscapeSettingsYAML.format(repo="AcademySoftwareFoundation/aswf-landscape"),
            body="""
global:
"""
            )
        responses.add(
            method=responses.GET,
            url=members.landscapeLandscapeYAML.format(repo="AcademySoftwareFoundation/aswf-landscape"),
            body="""
landscape:
  - category:
    name: ASWF Members
    subcategories:
      - subcategory:
        name: Premier
        items:
          - item:
            name: Academy of Motion Picture Arts and Sciences
            homepage_url: https://oscars.org/
            logo: academy_of_motion_picture_arts_and_sciences.svg
            twitter: https://twitter.com/TheAcademy
            crunchbase: https://www.crunchbase.com/organization/the-academy-of-motion-picture-arts-and-sciences
      - subcategory:
        name: Associate
        items:
          - item:
            name: Blender Foundation
            homepage_url: https://blender.org/
            logo: blender_foundation.svg
            twitter: https://twitter.com/Blender_Cloud
            crunchbase: https://www.crunchbase.com/organization/blender-org
"""
                )
        members.loadData()
        self.assertEqual(len(members.members),0)

    def testNormalizeLogo(self):
        members = LandscapeMembers(loadData = False)
        self.assertEqual(
            'https://raw.githubusercontent.com/dog/cat/master/hosted_logos/mouse.svg',
            members.normalizeLogo('mouse.svg','dog/cat')
        )

    def testNormalizeLogoIsEmpty(self):
        members = LandscapeMembers(loadData = False)
        self.assertEqual(
            '',
            members.normalizeLogo('','dog/cat')
        )
        self.assertEqual(
            '',
            members.normalizeLogo(None,'dog/cat')
        )

    def testNormalizeLogoIsURL(self):
        members = LandscapeMembers(loadData = False)
        self.assertEqual(
            'https://foo.com/mouse.svg',
            members.normalizeLogo('https://foo.com/mouse.svg','dog/cat')
        )

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("debug.log"),
        ]
    )
    
    unittest.main()
