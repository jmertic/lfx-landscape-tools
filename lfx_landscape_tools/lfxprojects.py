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

    def _should_skip_record(self, record):
        """Helper method to encapsulate the filtering logic."""
        return (
            self.find(name=record.get('Name'), homepage_url=record.get('Website'), slug=record.get('Slug')) or
            (self.activeOnly and record.get('Status') != 'Active') or
            not record.get('DisplayOnWebsite') or
            record.get('TestRecord') or
            record.get('Slug') == self.project
        )

    def _assign_category(self, member, category):
        """Helper method to map the record's category to landscape project levels."""
        if not (self.addCategory and category):
            return

        logger = logging.getLogger()
        logger.debug(f"Trying to see if project level {category} is valid")

        for project_level in self.landscapeProjectsLevels:
            if project_level.get('name') == category:
                member.project = project_level.get('level')
                member.membership = project_level.get('name')
                logger.debug("Project level is {} - {}".format(member.project, member.membership))
                break

    def _build_second_paths(self, record):
        """Helper method to evaluate and build the second_path array."""
        second_path = []

        if self.addParentProject:
            parent_slug = record.get('ParentSlug', self.project)
            parent_project = self.lookupParentProjectBySlug(parent_slug)
            if parent_project and "Membership" in parent_project.get("Model", []):
                cleaned_name = parent_project.get("Name", "").replace("/", ":")
                second_path.append('Project Group / {}'.format(cleaned_name))

        if self.addPMOManagedStatus and record.get('HasProgramManager'):
            second_path.append('PMO Managed / All')

        if self.addIndustrySector and record.get('IndustrySector'):
            cleaned_sector = record['IndustrySector'].replace("/", ":")
            second_path.append('Industry / {}'.format(cleaned_sector))

        if self.addTechnologySector and record.get('TechnologySector'):
            for sector in record['TechnologySector'].split(";"):
                cleaned_sector = sector.replace("/", ":")
                second_path.append('Technology Sector / {}'.format(cleaned_sector))

        return second_path

    def _process_record(self, record):
        """Helper method to handle the construction of a single Member object."""
        logger = logging.getLogger()

        member = Member()
        member.membership = 'All'
        member.name = record.get('Name')
        logger.info("Found LFX Project '{}'".format(member.name))

        # Set core attributes
        member.license = record.get('PrimaryOpenSourceLicense')
        member.repo_url = record.get('RepositoryURL')
        member.description = record.get('Description')

        member.homepage_url = record.get('Website')
        if not member.homepage_url and record.get('RepositoryURL'):
            logger.debug("Trying to use 'RepositoryURL' for 'homepage_url' instead")
            member.homepage_url = record.get('RepositoryURL')

        member.logo = record.get('ProjectLogo')
        if not member.logo:
            logger.info("Creating text logo for '{}'".format(member.name))
            member.logo = SVGLogo(name=member.name)

        # Optional: Provide a fallback using getattr if defaultCrunchbase is a class attribute
        member.crunchbase = record.get('CrunchBaseUrl', getattr(self, 'defaultCrunchbase', None))
        member.linkedin = record.get('LinkedIn')
        member.twitter = record.get('Twitter')

        self._assign_category(member, record.get('Category'))
        member.second_path = self._build_second_paths(record)

        # Build extra dictionary
        lfx_slug = record.get('Slug')
        parent_slug = record.get('ParentSlug', self.project)

        extra = {
            'lfx_slug': lfx_slug,
            'accepted': record.get('StartDate'),
            'archived': record.get('ProjectEntityDissolutionDate'),
            'facebook_url': record.get('Facebook'),
            'reddit_url': record.get('Reddit'),
            'pinterest_url': record.get('Pinterest'),
            'youtube_url': record.get('YouTube'),
            'dev_stats_url': self.lfxinsightsUrl.format(parent_slug=parent_slug, slug=lfx_slug),
            'annotations': {}
        }

        if self.artworkRepoUrl:
            extra['artwork_url'] = self.artworkRepoUrl.format(slug=lfx_slug)

        extra['other_links'] = [
            {'name': 'Calendar', 'url': self.calendarUrl.format(slug=lfx_slug)},
            {'name': 'iCal', 'url': self.icalUrl.format(project_id=record.get('ProjectID'))},
            {'name': 'Charter', 'url': record.get('CharterURL')}
        ]

        member.extra = extra
        return member

    def loadData(self):
        """Main method to fetch and process LFX projects data."""
        logger = logging.getLogger()
        logger.info("Loading LFX Projects data for {}".format(self.project))

        session = requests_cache.CachedSession()
        project_param = self.project if self.projectsFilterByParentSlug else ''

        with session.get(self.endpointURL.format(project_param)) as endpointResponse:
            member_list = endpointResponse.json()

            for record in member_list.get('Data', []):
                # 1. Guard clause handles skips cleanly
                if self._should_skip_record(record):
                    logger.debug(f"Skipping '{record.get('Name')}'")
                    continue

                # 2. Record processing handled in isolation
                member = self._process_record(record)

                # Assume list append exists here based on standard patterns
                if hasattr(self, 'members'):
                    self.members.append(member)

    def lookupParentProjectBySlug(self, slug):
        session = requests_cache.CachedSession()
        if slug:
            with session.get(self.singleSlugEndpointUrl.format(slug=slug)) as endpointResponse:
                parent_project = endpointResponse.json()
                if len(parent_project.get('Data',[])) > 0:
                    return parent_project['Data'][0]
                logging.getLogger().warning("Couldn't find project for slug '{}'".format(slug))

        return False
