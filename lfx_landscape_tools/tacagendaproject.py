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
from datetime import datetime

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

    graphql_query = """
query($org: String!, $number: Int!) {
  organization(login: $org) {
    projectV2(number: $number) {
      items(first: 100) {
        nodes {
          content {
            ... on Issue { title createdAt url labels(first: 10) { nodes { name } } }
            ... on PullRequest { title createdAt url labels(first: 10) { nodes { name } } }
          }
          fieldValues(first: 20) {
            nodes {
              ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2FieldCommon { name } } }
              ... on ProjectV2ItemFieldTextValue { text field { ... on ProjectV2FieldCommon { name } } }
              ... on ProjectV2ItemFieldNumberValue { number field { ... on ProjectV2FieldCommon { name } } }
              ... on ProjectV2ItemFieldDateValue { date field { ... on ProjectV2FieldCommon { name } } }
              ... on ProjectV2ItemFieldIterationValue { title field { ... on ProjectV2FieldCommon { name } } }
            }
          }
        }
      }
    }
  }
}
"""

    jq_filter = """
[ .data.organization.projectV2.items.nodes[] |
  select(.content.labels.nodes != null and ([.content.labels.nodes[].name] | contains(["2-annual-review"]))) |
  {
    title: .content.title,
    url: .content.url,
    created: .content.createdAt,
    labels: ([.content.labels.nodes[].name] | join(", ")),
    custom_fields: ([.fieldValues.nodes[] | select(.field != null) | {(.field.name): (.name // .text // .number // .date // .title // "n/a")}] | add)
  }
]
"""

    def processConfig(self, config: type[Config]):
        self.parent_slug = config.slug
        self.defaultCrunchbase = config.projectsDefaultCrunchbase
        self.assignSIGs = config.projectsAssignSIGs
        if config.tacAgendaProjectUrl:
            urlparts = urlparse(config.tacAgendaProjectUrl).path.split('/')
            if urlparts and len(urlparts) > 3 and urlparts[1] == 'orgs' and urlparts[3] == 'projects':
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

        cmd = [
            "gh", "api", "graphql",
            "-f", f"org={self.gh_org}",
            "-F", f"number={self.gh_project_id}",
            "-f", f"query={self.graphql_query}",
            "-q", self.jq_filter
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        logger.debug(result.returncode)
        logger.debug(result.stdout)
        if result.returncode != 0:
            logger.error("Invalid response from gh client: '{}'".format(result.stderr))
            return None

        csvRows = []
        try:
            projectData = json.loads(result.stdout)
        except Exception as e:
            logger.debug(e)
            logger.error("Invalid json: '{}'".format(jsonProjectData))
            return None

        logger.info('Found {} records'.format(len(projectData)))

        for item in projectData:
            logger.info("Processing {}...".format(item.get('title')))
            member = Member()
            member.name = item.get('title').strip()
            member.crunchbase = self.defaultCrunchbase
            extra = {}
            annotations = {}
            extra['annual_review_date'] = item.get('custom_fields',{}).get('Last Review Date')
            extra['accepted'] = item.get('custom_fields',{}).get('Accepted','')
            extra['incubating'] = item.get('custom_fields',{}).get('Incubating')
            extra['graduated'] = item.get('custom_fields',{}).get('Graduated')
            extra['archived'] = item.get('custom_fields',{}).get('Archived')
            extra['annual_review_url'] = item.get('url')
            annotations['next_annual_review_date'] = item.get('custom_fields',{}).get('Scheduled Date')
            annotations['submitted_date'] = datetime.fromisoformat(item.get('created','').replace('Z', '')).date().strftime("%Y-%m-%d")
            projectdetailsfromlfxcommittee = self._lookupProjectAndCommitteeDetailsByLFXURL(item.get('custom_fields',{}).get('PCC TSC Committee URL',''))
            if self.assignSIGs and projectdetailsfromlfxcommittee.get('category') != 'SIG':
                member.second_path = ['SIG / {}'.format(item.get('custom_fields',{}).get('SIG','No SIG'))]
            extra['lfx_slug'] = projectdetailsfromlfxcommittee.get('slug')
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
