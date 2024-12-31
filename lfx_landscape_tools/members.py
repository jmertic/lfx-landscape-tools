#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

## built in modules
import re
from abc import ABC, abstractmethod
from typing import Self
import logging

## third party modules
from url_normalize import url_normalize

from lfx_landscape_tools.config import Config

#
# Abstract Members class to normalize the methods used for the other ways of getting a member's info
#
class Members(ABC):

    def __init__(self, config: type[Config], loadData = True):
        self.processConfig(config)
        self.members = []
        if loadData:
            self.loadData()

    @abstractmethod
    def processConfig(self, config: type[Config]):
        pass

    @abstractmethod
    def loadData(self):
        pass

    def find(self, name, homepage_url, slug = None, membership = None, repo_url = None):
        '''
        Find Member object in this Members object that match the criteria given.

        Matches in this order - slug, membership+name+homepage_url, repo_url+name+homepage_url, name+homepage_url
        '''
        normalizedname = self.normalizeName(name)
        normalizedhomepage_url = self.normalizeURL(homepage_url)
        normalizedrepo_url = self.normalizeURL(homepage_url)
        
        logger = logging.getLogger()
        logger.debug("Looking for '{}'".format(normalizedname))

        members = []
        for member in self.members:
            logger.debug(member.name)
            logger.debug(member.extra.get('annotations',{}).get('slug'))
            if slug:
                if member.extra.get('annotations',{}).get('slug') and member.extra.get('annotations',{}).get('slug') == slug:
                    logger.debug("Found '{}' by slug '{}'".format(member.name,member.extra.get('annotations',{}).get('slug')))
                    members.append(member)
            elif membership:
                if ( self.normalizeName(member.name) == normalizedname or member.homepage_url == normalizedhomepage_url ) and member.membership == membership:
                    logger.debug("Found '{}' by membership '{}' and homepage_url '{}'".format(member.name,member.membership,member.homepage_url))
                    members.append(member)
            elif repo_url:
                if ( self.normalizeName(member.name) == normalizedname or member.homepage_url == normalizedhomepage_url or member.repo_url == normalizedrepo_url):
                    logger.debug("Found '{}' by repo_url '{}' and homepage_url '{}'".format(member.name,member.repo_url,member.homepage_url))
                    members.append(member)
            else:
                if ( self.normalizeName(member.name) == normalizedname or member.homepage_url == normalizedhomepage_url ):
                    logger.debug("Found '{}' by homepage_url '{}'".format(member.name,member.homepage_url))
                    members.append(member)
                
        return members
    
    def overlay(self, memberstooverlay: Self):
        '''
        Overlay another Members data onto this Members; if something is in the other
        Member that is in this member, it will NOT be added
        
        Keyword arguments:
        memberstooverlay -- the Members object to override this Members data values
        '''
        logging.getLogger().debug("Overlaying items")
        for member in self.members:
            logging.getLogger().debug("Checking matching item to overlay '{}'".format(member.name)) 
            foundmembers = []
            foundmembers = memberstooverlay.find(name=member.name,homepage_url=member.homepage_url,slug=member.extra.get('annotations',{}).get('slug'))
            for foundmember in foundmembers:
                logging.getLogger().debug("Found item to check for overlay '{}'".format(foundmember.name)) 
                member.overlay(foundmember)

    def normalizeName(self, name):
        if name is None:
            return ''

        name = name.replace(', Inc.','')
        name = name.replace(', Ltd','')
        name = name.replace(',Ltd','')
        name = name.replace(' Inc.','')
        name = name.replace(' Co.','')
        name = name.replace(' Corp.','')
        name = name.replace(' AB','')
        name = name.replace(' AG','')
        name = name.replace(' BV','')
        name = name.replace(' Pty Ltd','')
        name = name.replace(' Pte Ltd','')
        name = name.replace(' Ltd','')
        name = name.replace(', LLC','')
        name = name.replace(' LLC','')
        name = name.replace(' LLP','')
        name = name.replace(' SPA','')
        name = name.replace(' GmbH','')
        name = name.replace(' PBC','')
        name = name.replace(' Limited','')
        name = name.replace(' s.r.o.','')
        name = name.replace(' srl','')
        name = name.replace(' s.r.l.','')
        name = name.replace(' a.s.','')
        name = name.replace(' S.A.','')
        name = name.replace('.','')
        name = name.replace(' (member)','')
        name = name.replace(' (supporter)','')
        name = re.sub(r'\(.*\)','',name)

        return name.strip()

    def normalizeURL(self, url):
        return url_normalize(url)
