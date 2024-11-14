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
            for record in memberList:
                if self.find(record.get('Name'),record.get('Website'),record.get('Membership',{}).get('Name')) or self._isTestRecord(record):
                    continue

                member = Member()
                member.orgname = record.get('Name')
                logger.info("Found LFX Member '{}'".format(member.orgname))
                member.membership = record.get('Membership',{}).get('Name')
                member.website = record.get('Website')
                member.logo = record.get('Logo')
                if not member.logo:
                    logger.info("Trying to create text logo")
                    member.logo = SVGLogo(name=member.orgname)
                member.crunchbase = record.get('CrunchBaseURL')
                member.twitter = record.get('Twitter')
                member.linkedin = record.get('LinkedInURL')
                self.members.append(member)

    def find(self, org, website, membership = None):
        normalizedorg = self.normalizeCompany(org)
        normalizedwebsite = self.normalizeURL(website)

        members = []
        for member in self.members:
            if ( self.normalizeCompany(member.orgname) == normalizedorg or member.website == website) and member.membership == membership:
                members.append(member)

        return members

    def _isTestRecord(self,record):
        return record.get('Name') == "Test account" or record.get('ID') == '0012M00002WQimKQAT'
