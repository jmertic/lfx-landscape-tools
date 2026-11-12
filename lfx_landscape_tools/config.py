#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

## built in modules
import sys
import os
import io
import logging

## third party modules
import ruamel.yaml
import requests
import requests_cache

class Config:

    project = None
    view = 'members'
    slug = None
    landscape_members_category = 'Members'
    landscape_members_subcategories = [
        {"name": "Premier Membership", "category": "Premier"},
        {"name": "General Membership", "category": "General"},
    ]
    landscape_projects_levels = [
        {"name": "Active", "level": "active"},
        {"name": "Incubation", "level": "incubation"},
        {"name": "Sandbox", "level": "sandbox"},
    ]
    landscape_projects_category = 'Projects'
    landscape_projects_subcategories = [
       {"name": "All", "category": "All"}
    ]
    basedir = "."
    landscapefile = 'landscape.yml'
    missingcsvfile = 'missing.csv'
    hosted_logos_dir = 'hosted_logos'
    member_suffix = ''
    member_use_public_membership_logo = False
    projects_add_technology_sector = False
    projects_add_industry_sector = False
    projects_add_pmo_managed_status = False
    projects_add_parent_project = False
    projects_add_category = True
    projects_default_crunchbase = 'https://www.crunchbase.com/organization/linux-foundation'
    projects_filter_by_parent_slug = True
    projects_assign_sigs = False
    tac_agenda_project_url = None
    artwork_repo_url = None
    add_other_project_memberships = False

    def __init__(self, config_file: io.TextIOWrapper = None, view = None):
        if config_file:
            data_loaded = ruamel.yaml.YAML(typ='safe', pure=True).load(config_file)
            self.view = view if self._is_valid_view_option(view) else Config.view
            self.basedir = data_loaded.get('basedir',os.path.dirname(os.path.normpath(config_file.name)))
            self.slug = data_loaded.get('slug',self._lookup_slug_from_project(data_loaded.get('project')))
            self.project = data_loaded.get('project',self._lookup_project_from_slug(self.slug))
            if not self.slug or not self.project:
                raise ValueError("Invalid project specification in config file")
            self.landscape_projects_category = data_loaded.get('landscapeProjectsCategory',Config.landscape_projects_category)
            self.landscape_projects_levels = data_loaded.get('landscapeProjectsLevels',Config.landscape_projects_levels)
            self.landscape_projects_subcategories = data_loaded.get('landscapeProjectsSubcategories',self._get_landscape_projects_subcategories_from_levels())
            self.landscape_members_category = data_loaded.get('landscapeMembersCategory',Config.landscape_members_category)
            self.landscape_members_category = data_loaded.get('landscapeMemberCategory',Config.landscape_members_category)
            self.landscape_members_subcategories = data_loaded.get('landscapeMembersSubcategories',Config.landscape_members_subcategories)
            self.landscape_members_subcategories = data_loaded.get('landscapeMemberClasses',Config.landscape_members_subcategories)
            self.landscapefile = data_loaded.get('landscapefile',Config.landscapefile)
            self.missingcsvfile = data_loaded.get('missingcsvfile',Config.missingcsvfile)
            self.hosted_logos_dir = data_loaded.get('hostedLogosDir',Config.hosted_logos_dir)
            self.member_suffix = data_loaded.get('memberSuffix',Config.member_suffix)
            self.member_use_public_membership_logo = data_loaded.get('memberUsePublicMembershipLogo',Config.member_use_public_membership_logo)
            self.projects_add_technology_sector = data_loaded.get('projectsAddTechnologySector',Config.projects_add_technology_sector)
            self.projects_add_industry_sector = data_loaded.get('projectsAddIndustrySector',Config.projects_add_industry_sector)
            self.projects_add_pmo_managed_status = data_loaded.get('projectsAddPMOManagedStatus',Config.projects_add_pmo_managed_status)
            self.projects_add_parent_project = data_loaded.get('projectsAddParentProject',Config.projects_add_parent_project)
            self.projects_add_category = data_loaded.get('projectsAddCategory',Config.projects_add_category)
            self.projects_default_crunchbase = data_loaded.get('projectsDefaultCrunchbase',Config.projects_default_crunchbase)
            self.projects_filter_by_parent_slug = data_loaded.get('projectsFilterByParentSlug',Config.projects_filter_by_parent_slug)
            self.projects_assign_sigs = data_loaded.get('projectsAssignSIGs',Config.projects_assign_sigs)
            self.tac_agenda_project_url = data_loaded.get('tacAgendaProjectUrl',Config.tac_agenda_project_url)
            self.artwork_repo_url = data_loaded.get('artworkRepoUrl',Config.artwork_repo_url)
            self.add_other_project_memberships = data_loaded.get('addOtherProjectMemberships',Config.add_other_project_memberships)

    def _is_valid_view_option(self,view):
        return view in ['projects','members']

    @property
    def landscape_category(self):
        mapping = {
            'projects': self.landscape_projects_category,
            'members': self.landscape_members_category
        }
        return mapping.get(self.view)

    @property
    def landscape_subcategories(self):
        mapping = {
            'projects': self.landscape_projects_subcategories,
            'members': self.landscape_members_subcategories
        }
        return mapping.get(self.view)

    def _lookup_project_from_slug(self, slug):
        single_slug_endpoint_url = 'https://api-gw.platform.linuxfoundation.org/project-service/v1/public/projects?slug={}'
        session = requests_cache.CachedSession()
        if slug:
            with session.get(single_slug_endpoint_url.format(slug)) as endpointResponse:
                parent_project = endpointResponse.json()
                if len(parent_project.get('Data')) > 0:
                    return parent_project.get('Data')[0].get("ProjectID")

        logging.getLogger().warning("Couldn't find project for slug '{}'".format(slug))

        return None

    def _lookup_slug_from_project(self,project):
        single_project_endpoint_url = 'https://api-gw.platform.linuxfoundation.org/project-service/v1/public/projects?$filter=projectId%20eq%20{}'
        session = requests_cache.CachedSession()
        if project:
            with session.get(single_project_endpoint_url.format(project)) as endpointResponse:
                parent_project = endpointResponse.json()
                if len(parent_project.get('Data')) > 0:
                    return parent_project.get('Data',[])[0].get("Slug")

        logging.getLogger().warning("Couldn't find slug for project '{}'".format(project))

        return None

    def _get_landscape_projects_subcategories_from_levels(self):
        for level in self.landscape_projects_levels:
            self.landscape_projects_subcategories.append({'name':level['name'],'category':level['name']})
