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

    pcc_committee_url = 'https://api-gw.platform.linuxfoundation.org/project-service/v2/public/projects/{project_id}/committees/{committee_id}/members?$filter=role%20ne%20None&orderBy=Role'
    gh_cli_call = "gh project item-list {gh_project_id} --owner {gh_org} --format json --limit 200"

    def processConfig(self, config: type[Config]):
        self.parent_slug = config.slug
        self.defaultCrunchbase = config.projectsDefaultCrunchbase
        self.assignSIGs = config.projectsAssignSIGs
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

        logger.info('Found {} records'.format(len(projectData.get('items',[]))))

        for item in projectData.get('items',[]):
            found = False
            for label in item.get('labels',{}):
                if label.startswith('2-annual-review'):
                    found = True
                    continue;
            if not found:
                logger.debug("Skipping '{}'".format(item.get('content',{}).get('title').strip()))
                continue

            logger.info("Processing {}...".format(item.get('content',{}).get('title')))
            member = Member()
            member.name = item.get('content',{}).get('title').strip()
            member.crunchbase = self.defaultCrunchbase
            extra = {} 
            annotations = {}
            extra['annual_review_date'] = item.get('last Review Date')
            extra['accepted'] = item.get('accepted')
            extra['incubating'] = item.get('incubating')
            extra['graduated'] = item.get('graduated')
            extra['archived'] = item.get('archived')
            extra['annual_review_url'] = item.get('content',{}).get('url')
            annotations['next_annual_review_date'] = item.get('scheduled Date')
            projectdetailsfromlfxcommittee = self._lookupProjectAndCommitteeDetailsByLFXURL(item.get('pCC TSC Committee URL',''))
            if self.assignSIGs and projectdetailsfromlfxcommittee.get('category') != 'SIG':
                member.second_path = ['SIG / {}'.format(item.get('sIG','No SIG'))]
            annotations['slug'] = projectdetailsfromlfxcommittee.get('slug')
            session = requests_cache.CachedSession()
            chair = []
            if projectdetailsfromlfxcommittee.get('project_id') and projectdetailsfromlfxcommittee.get('committee_id'):
                with session.get(self.pcc_committee_url.format(
                        project_id=projectdetailsfromlfxcommittee.get('project_id'), \
                        committee_id=projectdetailsfromlfxcommittee.get('committee_id'))) \
                        as endpointResponse:
                    try:
                        memberList = endpointResponse.json()
                        for record in memberList.get('Data',[]):
                            if record.get('Role') in ['Chair','Vice Chair']:
                                logger.info("Found '{} {}' for the role '{}".format(record.get('FirstName').title(),record.get('LastName').title(),record.get('Role')))
                                chair.append('{} {}'.format(record.get('FirstName').title(),record.get('LastName').title()))
                            elif record.get('Role') == 'TAC/TOC Representative':
                                annotations["TAC_representative"] = '{} {}'.format(record.get('FirstName').title(),record.get('LastName').title())
                    except Exception as e:
                        logger.error("Couldn't load TSC Committee data for '{project}' - {error}".format(project=member.name,error=e))
            annotations['chair'] = ", ".join(chair)
            extra['annotations'] = annotations
            member.extra = extra
            self.members.append(member)

    def _lookupProjectAndCommitteeDetailsByLFXURL(self,url):
        urlparts = urlparse(url).path.split('/')
        if isinstance(urlparts,list) and len(urlparts) == 6 and urlparts[1] == 'project' and urlparts[3] == 'collaboration' and urlparts[4] == 'committees':
            singleProjectEndpointURL = 'https://api-gw.platform.linuxfoundation.org/project-service/v1/public/projects?$filter=projectId%20eq%20{}'
            session = requests_cache.CachedSession()
            with session.get(singleProjectEndpointURL.format(urlparts[2])) as endpointResponse:
                parentProject = endpointResponse.json()
                if len(parentProject.get('Data')) > 0: 
                    return {'project_id': urlparts[2],'committee_id': urlparts[5],'slug': parentProject.get('Data')[0]["Slug"],'category': parentProject.get('Data')[0].get('Category')}
        
        logging.getLogger().warning("Couldn't find project information with LFX URL '{}'".format(url)) 

        return {}
