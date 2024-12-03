#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

import logging
import json
import os
import subprocess

# third party modules
import requests
import requests_cache
from urllib.parse import urlparse

from lfx_landscape_tools.members import Members
from lfx_landscape_tools.member import Member
from lfx_landscape_tools.svglogo import SVGLogo
from lfx_landscape_tools.config import Config

class TACAgendaProject(Members):

    gh_project_id = None
    gh_org = None
    parent_slug = None

    pcc_committee_url = 'https://api-gw.platform.linuxfoundation.org/project-service/v2/public/projects/{project_id}/committees/{committee_id}/members'
    gh_cli_call = "gh project item-list {gh_project_id} --owner {gh_org} --format json --limit 200"

    def processConfig(self, config: type[Config]):
        self.parent_slug = config.slug
        self.defaultCrunchbase = config.projectsDefaultCrunchbase
        if config.tacAgendaProjectUrl:
            urlparts = urlparse(config.tacAgendaProjectUrl).path.split('/')
            if urlparts and urlparts[1] == 'orgs' and urlparts[3] == 'projects':
                self.gh_org = urlparts[2]
                self.gh_project_id = urlparts[4]

    def loadData(self):
        logger = logging.getLogger()
        logger.info("Loading TAC Agenda Project data")
        
        if not self.gh_project_id or not self.gh_org:
            id = self.gh_project_id if self.gh_project_id else ''
            org = self.gh_org if self.gh_org else ''
            logger.error("Cannot find GitHub Project - ID:{id} Org:{org}".format(id=id,org=org))
            return None

        command = subprocess.run(self.gh_cli_call.format(gh_project_id=self.gh_project_id,gh_org=self.gh_org), shell=True, capture_output=True)
        jsonProjectData = command.stdout
        csvRows = []
        try:
            projectData = json.loads(jsonProjectData)
        except:
            logger.error("Invalid response from gh client: '{}'".format(command.stderr))
            return None

        for item in projectData.get('items',[]):
            if '2-annual-review' not in item.get('labels',{}):
                continue

            logger.info("Processing {}...".format(item.get('content',{}).get('title')))
            member = Member()
            member.orgname = item.get('content',{}).get('title').strip()
            member.crunchbase = self.defaultCrunchbase
            extra = {} 
            annotations = {}
            extra['annual_review_date'] = item.get('last Review Date')
            annotations['slug'] = item.get('slug',self._lookupSlugByProjectID(item.get('pCC Project ID')))
            extra['annual_review_url'] = item.get('content',{}).get('url')
            annotations['next_annual_review_date'] = item.get('scheduled Date')
            session = requests_cache.CachedSession()
            chair = []
            if item.get('pCC Project ID') and item.get('pCC TSC Committee ID'):
                with session.get(self.pcc_committee_url.format(project_id=item.get('pCC Project ID'),committee_id=item.get('pCC TSC Committee ID'))) as endpointResponse:
                    try:
                        memberList = endpointResponse.json()
                        for record in memberList.get('Data',[]):
                            if record.get('Role') in ['Chair','Vice Chair']:
                                logger.debug("Found '{} {}' for the role '{}".format(record.get('FirstName').title(),record.get('LastName').title(),record.get('Role')))
                                chair.append('{} {}'.format(record.get('FirstName').title(),record.get('LastName').title()))
                    except Exception as e:
                        logger.error("Couldn't load TSC Committee data for '{project}' - {error}".format(project=member.orgname,error=e))
            annotations['chair'] = ", ".join(chair)
            extra['annotations'] = annotations
            member.extra = extra
            self.members.append(member)

    def _lookupSlugByProjectID(self,project):
        singleProjectEndpointURL = 'https://api-gw.platform.linuxfoundation.org/project-service/v1/public/projects?$filter=projectId%20eq%20{}'
        session = requests_cache.CachedSession()
        if project:
            with session.get(singleProjectEndpointURL.format(project)) as endpointResponse:
                parentProject = endpointResponse.json()
                if len(parentProject.get('Data')) > 0: 
                    return parentProject.get('Data')[0]["Slug"]
        
        logging.getLogger().warning("Couldn't find slug for project '{}'".format(project)) 
        
        return None
