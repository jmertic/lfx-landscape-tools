#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

import logging
from contextlib import suppress
import os
import re
from urllib.parse import urlparse

## third party modules
import ruamel.yaml
import requests

from lfx_landscape_tools.members import Members
from lfx_landscape_tools.member import Member
from lfx_landscape_tools.config import Config

class LandscapeMembers(Members):

    landscapeCategory = 'Members'
    landscapeSubcategories = [
        {"name": "Premier Membership", "category": "Premier"},
        {"name": "General Membership", "category": "General"},
        {"name": "Associate Membership", "category": "Associate"}
    ]
    landscapefile = 'landscape.yml'
    memberSuffix = ''

    def processConfig(self, config: type[Config]):
        self.landscapeCategory = config.landscapeCategory
        self.landscapeSubcategories = config.landscapeSubcategories
        self.landscapefile = os.path.join(config.basedir,config.landscapefile)
        self.memberSuffix = config.memberSuffix if config.view == 'members' else self.memberSuffix
        self.hostedLogosDir = os.path.join(config.basedir,config.hostedLogosDir)
        self.assignSIGs = config.projectsAssignSIGs

    def _load_landscape_yaml(self):
        """Helper method to load and parse the landscape YAML file."""
        logger = logging.getLogger()
        try:
            with open(self.landscapefile, 'r', encoding="utf8", errors='ignore') as f:
                logger.debug("Successfully opened landscape file '{}'".format(self.landscapefile))
                data = ruamel.yaml.YAML().load(f)
                logger.debug("Successfully parsed yaml output in landscape file '{}'".format(self.landscapefile))
                return data
        except Exception as e:
            logger.error("Error opening landscape file '{}' - will not load current landscape data - '{}'".format(self.landscapefile, e))
            return None

    def _process_member_item(self, item, subcategory_name):
        """Helper method to map a single YAML item to a Member object."""
        logger = logging.getLogger()
        member = Member()
        member.name = re.sub('{}$'.format(re.escape(self.memberSuffix)), '', item.get('name', ''))

        # Process Logo
        logo = item.get('logo')
        if logo:
            if urlparse(logo).scheme == '':
                member.logo = os.path.normpath("{}/{}".format(self.hostedLogosDir, logo))
            else:
                member.logo = logo

        logger.info("Found Landscape Member '{}'".format(member.name))

        # Dynamically set arbitrary attributes, skipping standard ones
        skip_keys = {'item', 'name', 'homepage_url', 'logo'}
        for key, value in item.items():
            if key not in skip_keys:
                logger.debug("Setting '{}' to '{}' for '{}'".format(key, value, member.name))
                setattr(member, key, value)

        # Match subcategory to determine membership
        for ls in self.landscapeSubcategories:
            if subcategory_name == ls.get('category'):
                logger.debug("Parsing subcategory '{}' to landscapeSubcategory '{}'".format(subcategory_name, ls.get('name')))
                member.membership = ls.get('name')
                break

        # Re-evaluate paths if assigning SIGs
        if self.assignSIGs and hasattr(member, 'second_path'):
            member.second_path = [p for p in member.second_path if not p.startswith('SIG /')]

        # Standard final attributes
        member.homepage_url = item.get('homepage_url')
        member.linkedin = item.get('extra', {}).get('linkedin_url')

        return member

    def loadData(self):
        """Main method to load landscape data into self.members."""
        logger = logging.getLogger()
        logger.info("Loading Current Landscape members in category '{}'".format(self.landscapeCategory))

        # 1. Load Data
        landscape = self._load_landscape_yaml()
        if not landscape:
            return

        # 2. Determine root category
        rootcategory = 'landscape' if landscape.get('landscape') else 'categories'

        # 3. Find the target category (flattens the first loop)
        categories = landscape.get(rootcategory, [])
        target_category = next((c for c in categories if c.get('name') == self.landscapeCategory), None)

        if not target_category:
            return

        # 4. Iterate and process members
        for subcategory in target_category.get('subcategories', []):
            subcat_name = subcategory.get('name')
            logger.debug("Processing subcategory '{}'...".format(subcat_name))

            for item in subcategory.get('items', []):
                member = self._process_member_item(item, subcat_name)
                self.members.append(member)
