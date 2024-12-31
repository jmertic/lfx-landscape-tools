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

    def loadData(self):
        logger = logging.getLogger()
        logger.info("Loading Current Landscape members in category '{}'".format(self.landscapeCategory))
        landscape = {}

        try:
            with open(self.landscapefile, 'r', encoding="utf8", errors='ignore') as fileobject: 
                logging.getLogger().debug("Successfully opened landscape file '{}'".format(self.landscapefile))
                landscape = ruamel.yaml.YAML().load(fileobject)
                logging.getLogger().debug("Successfully parsed yaml output in landscape file '{}'".format(self.landscapefile))
        except Exception as e:
            logging.getLogger().error("Error opening landscape file '{}' - will not load current landscape data - '{}'".format(self.landscapefile,e))
        else:
            for x in landscape.get('landscape',{}):
                if x.get('name') == self.landscapeCategory:
                    for subcategory in x.get('subcategories'):
                        logger.debug("Processing subcategory '{}'...".format(subcategory['name']))
                        for item in subcategory['items']:
                            member = Member()
                            member.name = re.sub('{}$'.format(re.escape(self.memberSuffix)),'',item.get('name'))
                            logger.info("Found Landscape Member '{}'".format(member.name))
                            for key, value in item.items():
                                if key not in ['item','name','homepage_url']:
                                    setattr(member, key, value)
                            for landscapeSubcategory in self.landscapeSubcategories:
                                if subcategory.get('name') == landscapeSubcategory.get('category'):
                                    logger.debug("Parsing subcategory '{}' to landscapeSubcategory '{}'".format(subcategory.get('name'),landscapeSubcategory.get('name')))
                                    member.membership = landscapeSubcategory.get('name')
                                    break

                            member.homepage_url = item.get('homepage_url')
                            member.linkedin = item.get('extra',{}).get('linkedin_url')
                            self.members.append(member)
                            break
