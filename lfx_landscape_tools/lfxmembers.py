#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

import logging

# third party modules
import requests

from lfx_landscape_tools.members import Members
from lfx_landscape_tools.member import Member
from lfx_landscape_tools.svglogo import SVGLogo
from lfx_landscape_tools.config import Config

class LFXMembers(Members):

    project = ''
    endpointURL = 'https://api-gw.platform.linuxfoundation.org/project-service/v1/public/projects/{}/members?orderBy=name&status=Active,At Risk' 
    endpointURLUsePublicMembershipLogo = 'https://api-gw.platform.linuxfoundation.org/project-service/v1/public/projects/{}/members?orderBy=name&status=Active,At Risk&usePublicMembershipLogo=true' 

    def processConfig(self, config: type[Config]):
        self.project = config.project
        self.endpointURL = self.endpointURLUsePublicMembershipLogo if config.memberUsePublicMembershipLogo else self.endpointURL

    def loadData(self):
        logger = logging.getLogger()
        logger.info("Loading LFX Members data")

        with requests.get(self.endpointURL.format(self.project)) as endpointResponse:
            memberList = endpointResponse.json()
            logger.info('Found {} records'.format(len(memberList)))
            for record in memberList:
                if self.find(name=record.get('Name'),homepage_url=record.get('Website'),membership=record.get('Membership',{}).get('Name')) or self._isTestRecord(record):
                    logger.debug("Skipping '{}'".format(record.get('Name')))
                    continue

                member = Member()
                member.name = record.get('Name')
                logger.info("Found LFX Member '{}'".format(member.name))
                member.membership = record.get('Membership',{}).get('Name')
                member.homepage_url = record.get('Website')
                member.description = record.get('OrganizationDescription')
                member.logo = record.get('Logo')
                if not member.logo:
                    logger.info("Creating text logo for '{}'".format(member.name))
                    member.logo = SVGLogo(name=member.name)
                member.crunchbase = record.get('CrunchBaseURL')
                member.twitter = record.get('Twitter')
                member.linkedin = record.get('LinkedInURL')
                self.members.append(member)

    def _isTestRecord(self,record):
        return record.get('Name') == "Test account" or record.get('ID') == '0012M00002WQimKQAT'
