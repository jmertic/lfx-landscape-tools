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

    landscape_category = 'Members'
    landscape_subcategories = [
        {"name": "Premier Membership", "category": "Premier"},
        {"name": "General Membership", "category": "General"},
        {"name": "Associate Membership", "category": "Associate"}
    ]
    landscapefile = 'landscape.yml'
    hosted_logos_dir = 'hosted_logos'
    member_suffix = ''

    _items_processed = 0
    _items_errors = 0

    def __init__(self, config: Config):
        self.landscape_items = []
        self.landscape_category = config.landscape_category
        self.landscape_subcategories = config.landscape_subcategories
        self.landscapefile = os.path.join(config.basedir,config.landscapefile)
        self.hosted_logos_dir = os.path.join(config.basedir,config.hosted_logos_dir)
        self.member_suffix = config.member_suffix if config.view == 'members' else self.member_suffix
        for landscape_subcategory in self.landscape_subcategories:
            subcategory = {
                "subcategory": None,
                "name": landscape_subcategory.get('category'),
                "items" : []
            }
            if subcategory not in self.landscape_items:
                self.landscape_items.append(subcategory)
    @property
    def items_processed(self):
        return self._items_processed

    @property
    def items_errors(self):
        return self._items_errors

    def load(self, members: Members):
        """
        Load Members into landscape_items
        Keyword arguments:
        members -- Members object to load
        """
        logger = logging.getLogger()
        logger.info(f"Processing '{self.landscape_category}' items")

        # Optimization: Map subcategory names to their parent categories once.
        # This eliminates the need for the 'next()' call inside the loop.
        subcat_to_parent = {s['name']: s['category'] for s in self.landscape_subcategories}

        for member in members.members:
            logger.info(f"Processing '{member.name}'...")

            # 1. Resolve target category using our map
            parent_cat_name = subcat_to_parent.get(member.membership)
            target_subcat = next((item for item in self.landscape_items
                                 if item['name'] == parent_cat_name), None)

            # Guard Clause: Category not found
            if not target_subcat:
                logger.error(f"Not adding '{member.name}' - SubCategory '{member.membership}' not found")
                self._items_errors += 1
                continue

            # Guard Clause: Validation check
            if not member.is_valid_landscape_item():
                missing = ",".join(member.invalid_landscape_item_attributes())
                logger.error(f"Not adding '{member.name}' - Missing key attributes {missing}")
                self._items_errors += 1
                continue

            logger.info(f"Added '{member.name}' to Landscape in SubCategory '{member.membership}'")
            self._items_processed += 1

            if self.member_suffix:
                member.entrysuffix = self.member_suffix

            member.host_logo(self.hosted_logos_dir)

            target_subcat['items'].append(member.to_landscape_item_attributes())

    def save(self):
        '''
        Save the landscape_items for a given landscape_category to the landscapefile
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
            logging.getLogger().exception("Error opening landscape file '{}'; will reset file - error message is '{}'".format(self.landscapefile,e))
            landscape = {
                'categories': [{
                    'name': self.landscape_category,
                    'subcategories': self.landscape_items
                }]
            }
        else:
            found = False
            rootcategory = 'categories'
            if landscape.get('landscape'):
                rootcategory = 'landscape'
            for x in landscape.get(rootcategory,[]):
                if x['name'] == self.landscape_category:
                    logging.getLogger().debug("Landscape Category '{}' found".format(self.landscape_category))
                    x['subcategories'] = self.landscape_items
                    found = True
                    continue

            if not found:
                logging.getLogger().debug("Landscape Category '{}' not found; adding it".format(self.landscape_category))
                landscape[rootcategory].append({
                    'category': None,
                    'name': self.landscape_category,
                    'subcategories': self.landscape_items
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
                ryaml.dump(landscape, fileobject, transform=self._remove_nulls)
            logging.getLogger().info("Successfully processed {} members and skipped {} members".format(self.items_processed,self.items_errors))

    def _remove_nulls(self,yamlout):
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
        return dumper.represent_plain_scalarstring(LiteralScalarString(data.strip()))

    def _none_representer(self, dumper, data):
        return dumper.represent_scalar(u'tag:yaml.org,2002:null', u'null')
