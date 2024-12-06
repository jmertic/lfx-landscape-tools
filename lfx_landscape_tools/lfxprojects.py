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
from urllib.parse import urlparse

from lfx_landscape_tools.members import Members
from lfx_landscape_tools.member import Member
from lfx_landscape_tools.svglogo import SVGLogo
from lfx_landscape_tools.config import Config

class LFXProjects(Members):

    project = '' 
    defaultCrunchbase = 'https://www.crunchbase.com/organization/linux-foundation'
    endpointURL = 'https://api-gw.platform.linuxfoundation.org/project-service/v1/public/projects?$filter=parentSlug%20eq%20{}&pageSize=2000&orderBy=name'
    singleSlugEndpointUrl = 'https://api-gw.platform.linuxfoundation.org/project-service/v1/public/projects?slug={slug}' 
    calendarUrl = 'https://zoom-lfx.platform.linuxfoundation.org/meetings/{slug}'
    icalUrl = 'https://webcal.prod.itx.linuxfoundation.org/lfx/{project_id}'
    lfxinsightsUrl = "https://insights.lfx.linuxfoundation.org/foundation/{parent_slug}/overview?project={slug}"
    artworkRepoUrl = None

    defaultCategory = ''
    defaultSubcategory = ''

    activeOnly = True
    addTechnologySector = True
    addIndustrySector = True
    addPMOManagedStatus = True
    addParentProject = True
    addCategory = True
    landscapeProjectsLevels = {}

    def processConfig(self, config: type[Config]):
        self.project = config.slug
        self.addTechnologySector = config.projectsAddTechnologySector
        self.addIndustrySector = config.projectsAddIndustrySector
        self.addPMOManagedStatus = config.projectsAddPMOManagedStatus
        self.addParentProject = config.projectsAddParentProject
        self.addCategory = config.projectsAddCategory
        self.defaultCrunchbase = config.projectsDefaultCrunchbase
        self.artworkRepoUrl = config.artworkRepoUrl
        self.projectsFilterByParentSlug = config.projectsFilterByParentSlug
        self.landscapeProjectsLevels = config.landscapeProjectsLevels

    def loadData(self):
        logger = logging.getLogger()
        logger.info("Loading LFX Projects data for {}".format(self.project))

        session = requests_cache.CachedSession()
        with session.get(self.endpointURL.format(self.project if self.projectsFilterByParentSlug else '')) as endpointResponse:
            memberList = endpointResponse.json()
            for record in memberList['Data']:
                if self.find(record.get('Name'),record.get('Website')):
                    continue
                if self.activeOnly and record['Status'] != 'Active':
                    continue
                if not record.get('DisplayOnWebsite'):
                    continue
                if record.get('TestRecord'):
                    continue

                second_path = []
                extra = {}
                annotations = {}
                member = Member()
                member.membership = 'All'
                member.orgname = record.get('Name')
                logger.info("Found LFX Project '{}'".format(member.orgname))
                annotations['slug'] = record.get('Slug')
                # Let's not include the root project
                if annotations.get('slug') == self.project:
                    continue
                member.repo_url = record.get('RepositoryURL')
                extra['accepted'] = record.get('StartDate')
                member.description = record.get('Description')
                if self.addCategory and record.get('Category'):
                    for projectLevel in self.landscapeProjectsLevels:
                        if projectLevel.get('name') == record.get('Category'):
                            member.project = projectLevel.get('level')
                            logger.debug("Project level is {}".format(member.project))
                            break
                member.website = record.get('Website')
                if not member.website:
                    logger.debug("Trying to use 'RepositoryURL' for 'website' instead")
                    member.website = record.get('RepositoryURL')
                if self.addParentProject:
                    parentName = self.lookupParentProjectNameBySlug(record.get('ParentSlug',self.project))
                    if parentName:
                        second_path.append('Project Group / {}'.format(parentName.replace("/",":")))
                member.logo = record.get('ProjectLogo')
                if not member.logo:
                    logger.debug("Trying to create text logo")
                    member.logo = SVGLogo(name=member.orgname)
                member.crunchbase = record.get('CrunchBaseUrl',self.defaultCrunchbase)
                member.linkedin = record.get('LinkedIn')
                member.twitter = record.get('Twitter')
                extra['facebook_url'] = record.get('Facebook')
                extra['reddit_url'] = record.get('Reddit')
                extra['pinterest_url'] = record.get('Pinterest')
                extra['youtube_url'] = record.get('YouTube')
                if self.addPMOManagedStatus and record.get('HasProgramManager'):
                    second_path.append('PMO Managed / All')
                if self.addIndustrySector and record.get('IndustrySector') != '':
                    second_path.append('Industry / {}'.format(record['IndustrySector'].replace("/",":")))
                if self.addTechnologySector and record.get('TechnologySector') != '':
                    sectors = record['TechnologySector'].split(";")
                    for sector in sectors:
                        second_path.append('Technology Sector / {}'.format(sector.replace("/",":")))
                extra['dev_stats_url'] = self.lfxinsightsUrl.format(parent_slug=record.get('ParentSlug',self.project),slug=annotations.get('slug'))
                annotations['calendar_url'] = self.calendarUrl.format(slug=annotations.get('slug'))
                annotations['ical_url'] = self.icalUrl.format(project_id=record.get('ProjectID'))
                if self.artworkRepoUrl:
                    extra['artwork_url'] = self.artworkRepoUrl.format(slug=annotations.get('slug'))
                extra['annotations'] = annotations
                member.extra = extra
                member.second_path = second_path
                self.members.append(member)

    def lookupParentProjectNameBySlug(self, slug):
        session = requests_cache.CachedSession()
        if slug:
            with session.get(self.singleSlugEndpointUrl.format(slug=slug)) as endpointResponse:
                parentProject = endpointResponse.json()
                if len(parentProject.get('Data',[])) > 0: 
                    return parentProject['Data'][0]["Name"]
                logging.getLogger().warning("Couldn't find project for slug '{}'".format(slug)) 
        
        return False

    def find(self, org, website, membership = None, repo_url = None):
        normalizedorg = self.normalizeCompany(org)
        normalizedwebsite = self.normalizeURL(website)

        members = []
        for member in self.members:
            if membership:
                if ( self.normalizeCompany(member.orgname) == normalizedorg or member.website == normalizedwebsite ) and member.membership == membership:
                    members.append(member)
            elif repo_url:
                if ( self.normalizeCompany(member.orgname) == normalizedorg or member.website == normalizedwebsite or member.repo_url == repo_url):
                    members.append(member)
            else:
                if ( self.normalizeCompany(member.orgname) == normalizedorg or member.website == normalizedwebsite ):
                    members.append(member)
                
        return members

