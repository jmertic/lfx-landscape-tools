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
    lfxinsightsUrl = "https://insights.linuxfoundation.org/project/{slug}"
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
                if self.find(name=record.get('Name'),homepage_url=record.get('Website'),slug=record.get('Slug')):
                    logger.debug("Skipping '{}'".format(record.get('Name')))
                    continue
                if self.activeOnly and record['Status'] != 'Active':
                    logger.debug("Skipping '{}'".format(record.get('Name')))
                    continue
                if not record.get('DisplayOnWebsite'):
                    logger.debug("Skipping '{}'".format(record.get('Name')))
                    continue
                if record.get('TestRecord'):
                    logger.debug("Skipping '{}'".format(record.get('Name')))
                    continue

                second_path = []
                extra = {}
                annotations = {}
                other_links = []
                member = Member()
                member.membership = 'All'
                member.name = record.get('Name')
                logger.info("Found LFX Project '{}'".format(member.name))
                extra['lfx_slug'] = record.get('Slug')
                member.license = record.get('PrimaryOpenSourceLicense')
                # Let's not include the root project
                if extra.get('lfx_slug') == self.project:
                    continue
                member.repo_url = record.get('RepositoryURL')
                extra['accepted'] = record.get('StartDate')
                member.description = record.get('Description')
                if self.addCategory and record.get('Category'):
                    for projectLevel in self.landscapeProjectsLevels:
                        if projectLevel.get('name') == record.get('Category'):
                            member.project = projectLevel.get('level')
                            member.membership = projectLevel.get('name')
                            logger.debug("Project level is {} - {}".format(member.project,member.membership))
                            break
                member.homepage_url = record.get('Website')
                if not member.homepage_url and record.get('RepositoryURL'):
                    logger.debug("Trying to use 'RepositoryURL' for 'homepage_url' instead")
                    member.homepage_url = record.get('RepositoryURL')
                if self.addParentProject:
                    parentProject = self.lookupParentProjectBySlug(record.get('ParentSlug',self.project))
                    if parentProject and "Membership" in parentProject.get("Model",[]):
                        second_path.append('Project Group / {}'.format(parentProject.get("Name").replace("/",":")))
                member.logo = record.get('ProjectLogo')
                if not member.logo:
                    logger.info("Creating text logo for '{}'".format(member.name))
                    member.logo = SVGLogo(name=member.name)
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
                extra['dev_stats_url'] = self.lfxinsightsUrl.format(parent_slug=record.get('ParentSlug',self.project),slug=extra.get('lfx_slug'))
                other_links.append({'name': 'Calendar','url': self.calendarUrl.format(slug=extra.get('lfx_slug'))})
                other_links.append({'name': 'iCal', 'url': self.icalUrl.format(project_id=record.get('ProjectID'))})
                other_links.append({'name': 'Charter', 'url': record.get('CharterURL')})
                if self.artworkRepoUrl:
                    extra['artwork_url'] = self.artworkRepoUrl.format(slug=extra.get('lfx_slug'))
                extra['annotations'] = annotations
                extra['other_links'] = other_links
                member.extra = extra
                member.second_path = second_path
                self.members.append(member)

    def lookupParentProjectBySlug(self, slug):
        session = requests_cache.CachedSession()
        if slug:
            with session.get(self.singleSlugEndpointUrl.format(slug=slug)) as endpointResponse:
                parentProject = endpointResponse.json()
                if len(parentProject.get('Data',[])) > 0: 
                    return parentProject['Data'][0]
                logging.getLogger().warning("Couldn't find project for slug '{}'".format(slug)) 
        
        return False
