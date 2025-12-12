#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

from lfx_landscape_tools.lfxprojects import LFXProjects

class LFXProjectsEU(LFXProjects):
    endpointURL = 'https://api-gw.platform.linuxfoundation.org/project-service/v1/public/projects?legalParentName=Linux%20Foundation%20Europe&pageSize=2000&orderBy=name'
