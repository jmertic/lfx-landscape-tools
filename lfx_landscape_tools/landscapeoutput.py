#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

## built in modules
import csv
import re
import logging
import os
from contextlib import suppress

## third party modules
import ruamel.yaml
from ruamel.yaml.scalarstring import LiteralScalarString, FoldedScalarString

from lfx_landscape_tools.config import Config
from lfx_landscape_tools.members import Members

class LandscapeOutput:

    landscapeCategory = 'Members'
    landscapeSubcategories = [
        {"name": "Premier Membership", "category": "Premier"},
        {"name": "General Membership", "category": "General"},
        {"name": "Associate Membership", "category": "Associate"}
    ]
    landscapefile = 'landscape.yml'
    hostedLogosDir = 'hosted_logos'
    memberSuffix = ''

    _itemsProcessed = 0
    _itemsErrors = 0

    def __init__(self, config: Config):
        self.landscapeItems = []
        self.landscapeCategory = config.landscapeCategory
        self.landscapeSubcategories = config.landscapeSubcategories
        self.landscapefile = os.path.join(config.basedir,config.landscapefile)
        self.hostedLogosDir = os.path.join(config.basedir,config.hostedLogosDir)
        self.memberSuffix = config.memberSuffix if config.view == 'members' else self.memberSuffix
        for landscapeSubcategory in self.landscapeSubcategories:
            subcategory = {
                "subcategory": None,
                "name": landscapeSubcategory.get('category'),
                "items" : []
            }
            if subcategory not in self.landscapeItems:
                self.landscapeItems.append(subcategory)
    @property
    def itemsProcessed(self):
        return self._itemsProcessed

    @property
    def itemsErrors(self):
        return self._itemsErrors

    def load(self, members: Members):
        """
        Load Members into landscapeItems
        Keyword arguments:
        members -- Members object to load
        """
        logger = logging.getLogger()
        logger.info(f"Processing '{self.landscapeCategory}' items")

        # Optimization: Map subcategory names to their parent categories once.
        # This eliminates the need for the 'next()' call inside the loop.
        subcat_to_parent = {s['name']: s['category'] for s in self.landscapeSubcategories}

        for member in members.members:
            logger.info(f"Processing '{member.name}'...")

            # 1. Resolve target category using our map
            parent_cat_name = subcat_to_parent.get(member.membership)
            target_subcat = next((item for item in self.landscapeItems
                                 if item['name'] == parent_cat_name), None)

            # Guard Clause: Category not found
            if not target_subcat:
                logger.error(f"Not adding '{member.name}' - SubCategory '{member.membership}' not found")
                self._itemsErrors += 1
                continue

            # Guard Clause: Validation check
            if not member.isValidLandscapeItem():
                missing = ",".join(member.invalidLandscapeItemAttributes())
                logger.error(f"Not adding '{member.name}' - Missing key attributes {missing}")
                self._itemsErrors += 1
                continue

            logger.info(f"Added '{member.name}' to Landscape in SubCategory '{member.membership}'")
            self._itemsProcessed += 1

            member.hostLogo(self.hostedLogosDir)

            if self.memberSuffix:
                member.entrysuffix = self.memberSuffix

            target_subcat['items'].append(member.toLandscapeItemAttributes())

    def save(self):
        '''
        Save the landscapeItems for a given landscapeCategory to the landscapefile
        '''
        # open existing landscape data file and see where to add the category data
        landscape = {}
        try:
            with open(self.landscapefile, 'r', encoding="utf8", errors='ignore') as fileobject:
                logging.getLogger().debug("Successfully opened landscape file '{}'".format(self.landscapefile))
                landscape = ruamel.yaml.YAML().load(fileobject)
                if not isinstance(landscape,dict) or landscape is None:
                    landscape = {}
                    raise RuntimeError('Landscape file is empty')
                logging.getLogger().debug("Successfully parsed yaml output in landscape file '{}'".format(self.landscapefile))
        except Exception as e:
            logging.getLogger().error("Error opening landscape file '{}'; will reset file - error message is '{}'".format(self.landscapefile,e))
            landscape = {
                'categories': [{
                    'name': self.landscapeCategory,
                    'subcategories': self.landscapeItems
                }]
            }
        else:
            found = False
            rootcategory = 'categories'
            if landscape.get('landscape'):
                rootcategory = 'landscape'
            for x in landscape.get(rootcategory,[]):
                if x['name'] == self.landscapeCategory:
                    logging.getLogger().debug("Landscape Category '{}' found".format(self.landscapeCategory))
                    x['subcategories'] = self.landscapeItems
                    found = True
                    continue

            if not found:
                logging.getLogger().debug("Landscape Category '{}' not found; adding it".format(self.landscapeCategory))
                landscape[rootcategory].append({
                    'category': None,
                    'name': self.landscapeCategory,
                    'subcategories': self.landscapeItems
                    })
        finally:
            with open(self.landscapefile, 'w+', encoding="utf8", errors='ignore') as fileobject:
                ryaml = ruamel.yaml.YAML(typ='rt')
                ryaml.Representer.add_representer(str,self._str_presenter)
                ryaml.Representer.add_representer(type(None),self._none_representer)
                ryaml.indent(mapping=2, sequence=4, offset=2)
                ryaml.default_flow_style = False
                ryaml.allow_unicode = True
                ryaml.width = 1000000
                ryaml.preserve_quotes = False
                ryaml.dump(landscape, fileobject, transform=self._removeNulls)
            logging.getLogger().info("Successfully processed {} members and skipped {} members".format(self.itemsProcessed,self.itemsErrors))

    def _removeNulls(self,yamlout):
        return yamlout.replace('- item: null','- item:') \
            .replace('- category: null','- category:') \
            .replace('- subcategory: null','- subcategory:') \
            .replace('\u2028',' ') \
            .replace('\x95','')

    def _str_presenter(self, dumper, data):
        if '\n' in data:
            return dumper.represent_literal_scalarstring(LiteralScalarString(data))
        if len(data.splitlines()) > 1:  # check for multiline string
            return dumper.represent_folded_scalarstring(FoldedScalarString(data))
        return dumper.represent_str(data)

    def _none_representer(self, dumper, data):
        return dumper.represent_scalar(u'tag:yaml.org,2002:null', u'null')
