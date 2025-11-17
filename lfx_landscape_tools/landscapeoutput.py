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
        '''
        Load Members into landscapeItems

        Keyword arguments:
        members -- Members object to load
        '''
        logger = logging.getLogger() 
        logger.info("Processing '{}' items".format(self.landscapeCategory))
        for member in members.members:
            logger.info("Processing '{}'...".format(member.name))
            foundCategory = False
            for landscapeItemSubcategory in self.landscapeItems:
                landscapeSubcategory = next((item for item in self.landscapeSubcategories if item["name"] == member.membership), None)
                if ( ( landscapeSubcategory is not None )
                        and ( landscapeSubcategory['name'] == member.membership ) 
                        and ( landscapeItemSubcategory['name'] == landscapeSubcategory['category'] ) ):
                    foundCategory = True
                    # Write out to error log if it's missing key parameters
                    if not member.isValidLandscapeItem():
                        logger.error("Not adding '{}' to Landscape - Missing key attributes {}".format(member.name,",".join(member.invalidLandscapeItemAttributes())))
                        self._itemsErrors += 1
                    # otherwise we can add it
                    else:
                        logger.info("Added '{}' to Landscape in SubCategory '{}'".format(member.name,member.membership))
                        self._itemsProcessed += 1
                        member.hostLogo(self.hostedLogosDir)
                        member.entrysuffix = self.memberSuffix if self.memberSuffix else member.entrysuffix
                        landscapeItemSubcategory['items'].append(member.toLandscapeItemAttributes())
                    break
            if not foundCategory:
                logger.error("Not adding '{}' to Landscape - SubCategory '{}' not found".format(member.name,member.membership))
                self._itemsErrors += 1

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

    def _removeNulls(self,yamlout):
        return yamlout.replace('- item: null','- item:') \
            .replace('- category: null','- category:') \
            .replace('- subcategory: null','- subcategory:') \
            .replace('\u2028',' ') \
            .replace('\x95','')

    def _str_presenter(self, dumper, data):
        if '\n' in data:
            return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='|')
        if len(data.splitlines()) > 1:  # check for multiline string
            return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='>')
        return dumper.represent_scalar(u'tag:yaml.org,2002:str', data)

    def _none_representer(self, dumper, data):
        return dumper.represent_scalar(u'tag:yaml.org,2002:null', u'null')
