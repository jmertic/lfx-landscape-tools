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

    landscape_category = 'Members'
    landscape_subcategories = [
        {"name": "Premier Membership", "category": "Premier"},
        {"name": "General Membership", "category": "General"},
        {"name": "Associate Membership", "category": "Associate"}
    ]
    landscapefile = 'landscape.yml'
    member_suffix = ''

    def processConfig(self, config: type[Config]):
        self.landscape_category = config.landscape_category
        self.landscape_subcategories = config.landscape_subcategories
        self.landscapefile = os.path.join(config.basedir,config.landscapefile)
        self.member_suffix = config.member_suffix if config.view == 'members' else self.member_suffix
        self.hosted_logos_dir = os.path.join(config.basedir,config.hosted_logos_dir)
        self.assignSIGs = config.projects_assign_sigs

    def load_landscape_yaml(self):
        """Helper method to load and parse the landscape YAML file."""
        logger = logging.getLogger()
        try:
            with open(self.landscapefile, 'r', encoding="utf8", errors='ignore') as f:
                logger.debug("Successfully opened landscape file '{}'".format(self.landscapefile))
                data = ruamel.yaml.YAML().load(f)
                logger.debug("Successfully parsed yaml output in landscape file '{}'".format(self.landscapefile))
                return data
        except Exception as e:
            logger.exception("Error opening landscape file '{}' - will not load current landscape data - '{}'".format(self.landscapefile, e))
            return None

    def _process_member_item(self, item, subcategory_name):
        """Helper method to map a single YAML item to a Member object."""
        logger = logging.getLogger()
        member = Member()
        member.name = re.sub('{}$'.format(re.escape(self.member_suffix)), '', item.get('name', ''))

        # Process Logo
        logo = item.get('logo')
        if logo:
            if urlparse(logo).scheme == '':
                member.logo = os.path.normpath("{}/{}".format(self.hosted_logos_dir, logo))
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
        for ls in self.landscape_subcategories:
            if subcategory_name == ls.get('category'):
                logger.debug("Parsing subcategory '{}' to landscape subcategory '{}'".format(subcategory_name, ls.get('name')))
                member.membership = ls.get('name')
                break

        # Re-evaluate paths if assigning SIGs
        if self.assignSIGs and hasattr(member, 'second_path'):
            member.second_path = [p for p in member.second_path if not p.startswith('SIG /')]

        # Standard final attributes
        member.homepage_url = item.get('homepage_url')
        member.linkedin = item.get('extra', {}).get('linkedin_url')

        return member

    def load_data(self):
        """Main method to load landscape data into self.members."""
        logger = logging.getLogger()
        logger.info("Loading Current Landscape members in category '{}'".format(self.landscape_category))

        # 1. Load Data
        landscape = self.load_landscape_yaml()
        if not landscape:
            return
        if not isinstance(landscape, dict):
            logger.error("Landscape file '{}' is not a mapping - will not load current landscape data".format(self.landscapefile))
            return

        # 2. Determine root category
        rootcategory = 'landscape' if landscape.get('landscape') else 'categories'

        # 3. Find the target category (flattens the first loop)
        categories = landscape.get(rootcategory) or []
        target_category = next((c for c in categories if isinstance(c, dict) and c.get('name') == self.landscape_category), None)

        if not target_category:
            return

        # 4. Iterate and process members
        for subcategory in target_category.get('subcategories') or []:
            if not isinstance(subcategory, dict):
                logger.error("Skipping malformed subcategory '{}' in category '{}'".format(subcategory, self.landscape_category))
                continue
            subcat_name = subcategory.get('name')
            logger.debug("Processing subcategory '{}'...".format(subcat_name))

            for item in subcategory.get('items') or []:
                if not isinstance(item, dict):
                    logger.error("Skipping malformed item '{}' in subcategory '{}'".format(item, subcat_name))
                    continue
                member = self._process_member_item(item, subcat_name)
                self.members.append(member)
