#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

import logging

# third party modules
import requests
import requests_cache

from lfx_landscape_tools.members import Members
from lfx_landscape_tools.member import Member
from lfx_landscape_tools.svglogo import SVGLogo
from lfx_landscape_tools.config import Config

class LFXMembers(Members):

    project = ''
    endpointURL = 'https://api-gw.platform.linuxfoundation.org/project-service/v1/public/projects/{}/members?orderBy=name&status=Active,At Risk' 
    endpointURLUsePublicMembershipLogo = 'https://api-gw.platform.linuxfoundation.org/project-service/v1/public/projects/{}/members?orderBy=name&status=Active,At Risk&usePublicMembershipLogo=true' 
    endpointURLAllAutoJoinProjects = 'https://api-gw.platform.linuxfoundation.org/project-service/v1/public/projects?autoJoinEnabled=true&pageSize=2000'

    def processConfig(self, config: type[Config]):
        self.project = config.project
        self.endpointURL = self.endpointURLUsePublicMembershipLogo if config.memberUsePublicMembershipLogo else self.endpointURL
        self.addOtherProjectMemberships = config.addOtherProjectMemberships 

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
                second_path = []
                member.membership = record.get('Membership',{}).get('Name')
                member.website = record.get('Website')
                member.logo = record.get('Logo')
                if not member.logo:
                    logger.info("Trying to create text logo")
                    member.logo = SVGLogo(name=member.orgname)
                member.crunchbase = record.get('CrunchBaseURL')
                member.twitter = record.get('Twitter')
                member.linkedin = record.get('LinkedInURL')
                if self.addOtherProjectMemberships:
                    for slug in self.projectsOnAutojoin:
                        session = requests_cache.CachedSession()
                        with session.get(self.endpointURL.format(slug)) as otherProjectMembershipsEndpointResponse:
                            for membership in otherProjectMembershipsEndpointResponse.json():
                                if membership.get('ID') == record.get('ID'):
                                    logger.info("Adding other membership - {}".format(membership.get("ProjectName")))
                                    second_path.append('Project Membership / {}'.format(membership.get("ProjectName")))
                member.second_path = second_path
                self.members.append(member)

    def find(self, org, website, membership = None):
        normalizedorg = self.normalizeCompany(org)
        normalizedwebsite = self.normalizeURL(website)

        members = []
        for member in self.members:
            if ( self.normalizeCompany(member.orgname) == normalizedorg or member.website == website) and member.membership == membership:
                members.append(member)

        return members

    @property
    def projectsOnAutojoin(self):
        session = requests_cache.CachedSession()
        slugs = []
        with session.get(self.endpointURLAllAutoJoinProjects) as endpointResponse:
            projects = endpointResponse.json()
            for project in projects['Data']:
                if self.project != project.get('Slug'):
                    slugs.append(project.get('Slug'))

        return slugs

    def _isTestRecord(self,record):
        return record.get('Name') == "Test account" or record.get('ID') == '0012M00002WQimKQAT'
