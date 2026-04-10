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

    def _get_other_project_memberships(self, record_id):
        """Helper to fetch memberships across other projects."""
        second_path = []
        if not self.addOtherProjectMemberships:
            return second_path

        session = requests_cache.CachedSession()
        for slug in self.projectsOnAutojoin:
            with session.get(self.endpointURL.format(slug)) as response:
                for membership in response.json():
                    if membership.get('ID') == record_id:
                        project_name = membership.get("ProjectName")
                        logging.getLogger().info(f"Adding other membership - {project_name}")
                        second_path.append(f'Project Membership / {project_name}')
        return second_path

    def loadData(self):
        logger = logging.getLogger()
        logger.info("Loading LFX Members data")

        with requests.get(self.endpointURL.format(self.project)) as endpointResponse:
            member_list = endpointResponse.json()
            logger.info(f'Found {len(member_list)} records')

            for record in member_list:
                name = record.get('Name')
                membership_name = record.get('Membership', {}).get('Name')

                if self._isTestRecord(record) or self.find(
                    name=name,
                    homepage_url=record.get('Website'),
                    membership=membership_name
                ):
                    logger.debug(f"Skipping '{name}'")
                    continue

                logger.info(f"Found LFX Member '{name}'")

                member = Member()
                member.name = name
                member.membership = membership_name
                member.homepage_url = record.get('Website')
                member.description = record.get('OrganizationDescription')
                member.logo = record.get('Logo') or SVGLogo(name=name)

                if not record.get('Logo'):
                    logger.info(f"Creating text logo for '{name}'")

                member.crunchbase = record.get('CrunchBaseURL')
                member.twitter = record.get('Twitter')
                member.linkedin = record.get('LinkedInURL')

                member.second_path = self._get_other_project_memberships(record.get('ID'))

                self.members.append(member)

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
