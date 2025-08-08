#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

## built in modules
import os
from urllib.parse import urlparse
import logging
import socket
from typing import Self

## third party modules
from url_normalize import url_normalize
import validators
import requests
import requests_cache
from github import Github, GithubException, RateLimitExceededException, Auth
import ruamel.yaml
from bs4 import BeautifulSoup

from lfx_landscape_tools.svglogo import SVGLogo

#
# Member object to ensure we have normalization on fields. Only fields that are required or need validation are defined; others can be added dynamically.
#
class Member:

    membership = None
    second_path = []
    organization = {}
    __extra = {}
    project = None
    project_org = None
    additional_repos = []
    __name = None
    __homepage_url = None
    __logo = None
    __crunchbase = None
    __linkedin = None
    __twitter = None
    __repo_url = None

    # config properties
    entrysuffix = ''

    # schema for items entries
    itemschema = []

    def __init__(self):
        # load in data schema from landscape2
        try:
            schemaURL = 'https://raw.githubusercontent.com/cncf/landscape2/refs/heads/main/docs/config/data.yml'
            endpointResponse = requests_cache.CachedSession().get(schemaURL)
            endpointResponse.raise_for_status() 
            dataschema = ruamel.yaml.YAML().load(endpointResponse.text)
        except requests.exceptions.RequestException as e:
            logging.getLogger().error("Cannot load data file schema at {} - error message '{}'".format(schemaURL,e))
        except ruamel.yaml.YAMLError as e: 
            logging.getLogger().error("Data file at {} is not valid YAML - error message '{}'".format(schemaURL,e))
        else:
            self.itemschema = dataschema.get('categories',{})[0].get('subcategories',{})[0].get('items',{})[0]

    def __dir__(self):
        returnvalue = list(self.itemschema.keys())
        returnvalue.append('linkedin')
        returnvalue.append('membership')
        returnvalue.append('project_org')
        return returnvalue

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name):
        if not name or name == '':
            name = None

        self.__name = name

    @property
    def repo_url(self):
        return self.__repo_url

    @repo_url.setter
    def repo_url(self, repo_url):
        if repo_url == '':
            self.__repo_url = None
        elif repo_url is not None:
            repo_url = url_normalize(repo_url.rstrip("/"), default_scheme='https')
            if self._isGitHubOrg(repo_url):
                logging.debug("{} is determined to be a GitHub Org for '{}' - finding related GitHub Repo".format(repo_url,self.name))
                try:
                    found_repo_url = self._getPrimaryGitHubRepoFromGitHubOrg(repo_url)
                    if found_repo_url:
                        self.project_org = "https://github.com/{}".format(urlparse(found_repo_url).path.split("/")[1])
                        self.__repo_url = found_repo_url 
                        logging.debug("{} is determined to be the associated GitHub Repo for GitHub Org {} for '{}'".format(self.__repo_url,self.project_org,self.name))
                    else:
                        self.project_org = None
                        self.__repo_url = None
                        logging.warning("No public repositories found in GitHub Org {} - not setting repo_url for '{}'".format(self.project_org,self.name))
                except ValueError as e:
                    self.project_org = None
                    self.__repo_url = None
                    logging.warning("No public repositories found in GitHub Org {} - not setting repo_url for '{}' - error message '{}'".format(self.project_org,self.name,e))
            elif self._isGitHubRepo(repo_url) or self._isGitHubURL(repo_url):
                # clean up to ensure it's a valid github repo url
                x = urlparse(repo_url)
                parts = x.path.split("/")
                self.__repo_url = "https://github.com/{}/{}".format(parts[1],parts[2])
                logging.debug("{} is determined to be a GitHub Repo for '{}'".format(self.__repo_url,self.name))
            else:
                logging.debug("{} is determined to be something else".format(repo_url))
                self.__repo_url = repo_url

    def _isGitHubURL(self, url):
        return urlparse(url).netloc == 'www.github.com' or urlparse(url).netloc == 'github.com'
    
    def _isGitHubRepo(self, url):
        return self._isGitHubURL(url) and len(urlparse(url).path.split("/")) == 3

    def _isGitHubOrg(self, url):
        return self._isGitHubURL(url) and len(urlparse(url).path.split("/")) == 2

    def _getPrimaryGitHubRepoFromGitHubOrg(self, url):
        if not self._isGitHubOrg(url):
            return list(url)

        if len(self._getPinnedGithubReposFromGithubOrg(url)) > 0:
            return self._getPinnedGithubReposFromGithubOrg(url)[0]

        with requests_cache.enabled():
            while True:
                try:
                    if 'GITHUB_TOKEN' in os.environ:
                        g = Github(auth=Auth.Token(os.environ['GITHUB_TOKEN']), per_page=1000)
                    else:
                        g = Github(per_page=1000)
                    repos = g.search_repositories(query="org:{}".format(urlparse(url).path.split("/")[1]),sort="stars",order="desc")
                    if len(list(repos)) > 0:
                        return repos[0].html_url
                    else:
                        return ''
                except RateLimitExceededException:
                    logging.info("Sleeping until we get past the API rate limit....")
                    time.sleep(g.rate_limiting_resettime-now())
                except GithubException as e:
                    if e.status == 502:
                        logging.debug("Server error - retrying...")
                    if e.status == 404:
                        return False
                    else:
                        logging.getLogger().warning(e.data)
                        return
                except socket.timeout:
                    logging.debug("Server error - retrying...")

    def _getPinnedGithubReposFromGithubOrg(self, url):
        if not self._isGitHubOrg(url):
            return list(url)

        repos = []

        try:
            orgPageResponse = requests_cache.CachedSession().get(url)
            orgPageResponse.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.getLogger().error("Cannot load {} - error message '{}'".format(url,e))
        else:
            soup = BeautifulSoup(orgPageResponse.text, 'html.parser')
            for item in soup.find_all("li",{"class": "js-pinned-item-list-item"}):
                repos.append("https://github.com{}".format(item.find("a").attrs['href']))

        return repos

    @property
    def linkedin(self):
        return self.__linkedin

    @linkedin.setter
    def linkedin(self, linkedin):
        if linkedin == '' or not linkedin:
            self.__linkedin = None
        # See if this is just the short form part of the LinkedIn URL
        elif linkedin.startswith('company'):
            self.__linkedin = "https://www.linkedin.com/{}".format(linkedin)
        # perhaps they forgot to add the https://
        elif linkedin.startswith('www.linkedin.com') or linkedin.startswith('linkedin.com'):
            self.__linkedin = "https://www.linkedin.com{}".format(urlparse(url_normalize(linkedin)).path)
        # If it is a URL, make sure it's properly formed
        elif ( urlparse(linkedin).netloc == 'linkedin.com' or urlparse(linkedin).netloc == 'www.linkedin.com' ):
            self.__linkedin = "https://www.linkedin.com{}".format(urlparse(linkedin).path)
        else:
            self.__linkedin = None
            logging.getLogger().warning("Member.linkedin for '{name}' must be set to a valid LinkedIn URL - '{linkedin}' provided".format(linkedin=linkedin,name=self.name))

    @property
    def crunchbase(self):
        return self.__crunchbase

    @crunchbase.setter
    def crunchbase(self, crunchbase):
        if crunchbase == '':
            self.__crunchbase = None
        elif crunchbase and ( urlparse(crunchbase).netloc == 'crunchbase.com' or urlparse(crunchbase).netloc == 'www.crunchbase.com' ) and urlparse(crunchbase).path.split("/")[1] == 'organization':
            self.__crunchbase = "https://www.crunchbase.com/{}/{}".format(urlparse(crunchbase).path.split('/')[1],urlparse(crunchbase).path.split('/')[2])
        else:
            self.__crunchbase = None
            logging.getLogger().warning("Member.crunchbase for '{name}' must be set to a valid Crunchbase URL - '{crunchbase}' provided".format(crunchbase=crunchbase,name=self.name))

    @property
    def homepage_url(self):
        return self.__homepage_url

    @homepage_url.setter
    def homepage_url(self, homepage_url):
        if homepage_url == '' or homepage_url is None:
            self.__homepage_url = None
            logging.getLogger().warning("Member.homepage_url must be not be blank for '{name}'".format(name=self.name))
        else:
            normalizedhomepage_url = url_normalize(homepage_url, default_scheme='https')
            if not validators.url(normalizedhomepage_url):
                self.__homepage_url = None
                logging.getLogger().warning("Member.homepage_url for '{name}' must be set to a valid homepage_url - '{homepage_url}' provided".format(homepage_url=homepage_url,name=self.name))
            else:
                self.__homepage_url = normalizedhomepage_url

    @property
    def logo(self):
        return self.__logo

    @logo.setter
    def logo(self, logo):
        if logo is None or logo == '':
            self.__logo = None
            logging.getLogger().warning("Member.logo must be not be blank for '{name}'".format(name=self.name))
            return
        elif type(logo) is SVGLogo:
            self.__logo = logo
        elif urlparse(logo).scheme != '':
            self.__logo = SVGLogo(url=logo)
        else:
            self.__logo = SVGLogo(filename=logo)

        if not self.__logo.isValid():
            self.__logo = None
            logging.getLogger().warning("Member.logo for '{name}' invalid format".format(name=self.name))
    
    def hostLogo(self, path = "./"):
        self.__logo.save(self.name,path)

    @property
    def twitter(self):
        return self.__twitter

    @twitter.setter
    def twitter(self, twitter):
        if not twitter or twitter == "":
            self.__twitter = None
        elif not twitter.startswith('https://twitter.com/'):
            # fix the URL if it's not formatted right
            o = urlparse(twitter)
            if o.netloc == '':
                self.__twitter = "https://twitter.com/{}".format(twitter)
            elif (o.netloc == "twitter.com" or o.netloc == "www.twitter.com"):
                self.__twitter = "https://twitter.com{path}".format(path=o.path)
            else:
                self.__twitter = None
                logging.getLogger().warning("Member.twitter for '{name}' must be either a Twitter handle, or the URL to a twitter handle - '{twitter}' provided".format(twitter=twitter,name=self.name))
        else:
            self.__twitter = twitter

    @property
    def extra(self):
        return self.__extra

    @extra.setter
    def extra(self, extra):
        if not isinstance(extra,dict):
            logging.getLogger().debug("Member.extra for '{name}' must be a list - '{extra}' provided".format(extra=extra,name=self.name))
            self.__extra = {}
        endextra = {}
        endannotations = {}
        for key, value in extra.items():
            # remove any entries where name or url is set to None
            if key == 'other_links' and isinstance(value,list):
                other_links = []
                for link in value:
                    if validators.url(link.get('url',False)) and link.get('name',False):
                        other_links.append(link)
                endextra['other_links'] = other_links
            elif not value or value == 'nil':
                logging.getLogger().debug("Removing Member.extra.{key} for '{name}' since it's set to '{value}'".format(key=key,value=value,name=self.name))
            elif key not in self.itemschema['extra']:
                logging.getLogger().debug("Moving Member.extra.{key} for '{name}' under 'annotations'".format(key=key,name=self.name))
                endannotations[key] = value
            else:
                endextra[key] = value

        endextraannotations = endextra.get('annotations',{}) | endannotations
        endextra['annotations'] = {key: value for key, value in endextraannotations.items() if value is not None}

        self.__extra = endextra

    def toLandscapeItemAttributes(self):
        returnentry = {'item': None}

        logging.getLogger().debug("Processing into landscape item attributes")
        for key,value in self.itemschema.items():
            if key == 'name':
                returnentry['name'] = "{}{}".format(self.name,self.entrysuffix)
            elif key == 'logo' and isinstance(self.__logo,SVGLogo):
                returnentry['logo'] = self.__logo.filename(self.name)
            elif not getattr(self,key,None):
                continue
            elif isinstance(value,dict):
                returnentry[key] = {}
                for subkey, subvalue in value.items():
                    if getattr(self,key,[]).get(subkey):
                        if isinstance(subvalue,dict) and subkey not in ['annotations']:
                            returnentry[key][subkey] = {}
                            for subsubkey, subsubvalue in subvalue.items():
                                if getattr(self,key,[]).get(subkey).get(subsubkey):
                                    returnentry[key][subkey][subsubkey] = getattr(self,key,[]).get(subkey).get(subsubkey)
                        else:    
                            returnentry[key][subkey] = getattr(self,key,[]).get(subkey)
                if returnentry[key] == {}:
                    del returnentry[key]
            else:
                returnentry[key] = getattr(self,key)
            logging.getLogger().debug("Setting '{}' to '{}'".format(key,returnentry.get(key)))

        if self.project_org:
            additional_repos = [] #returnentry.get('additional_repos',[])
            for repo_url in self._getPinnedGithubReposFromGithubOrg(self.project_org):
                if repo_url != self.repo_url:
                    additional_repos.append({'repo_url':repo_url})
            returnentry['additional_repos'] = additional_repos
            logging.getLogger().debug("Setting 'additional_repos' to '{}' for '{}'".format(returnentry.get('additional_repos'),self.name))
            # Put the project_org in annotations
            if self.project_org:
                if not returnentry.get('extra'):
                    returnentry['extra'] = {}
                if not returnentry['extra'].get('annotations'):
                    returnentry['extra']['annotations'] = {}
                returnentry['extra']['annotations']['project_org'] = self.project_org
                logging.getLogger().debug("Setting 'extra.annotations.project_org' to '{}' for '{}'".format(returnentry.get('extra',{}).get('annotations',{}).get('project_org'),self.name))

        if not self.crunchbase:
            logging.getLogger().debug("No Crunchbase entry for '{}' - specifying name instead".format(self.name))
            returnentry['organization'] = {}
            returnentry['organization']['name'] = self.name
            if self.linkedin:
                returnentry['organization']['linkedin'] = self.linkedin
            if returnentry.get('crunchbase'):
                del returnentry['crunchbase']

        if self.linkedin:
            logging.getLogger().debug("Setting 'extra.linkedin_url' to '{}' for '{}'".format(self.linkedin,self.name))
            if not returnentry.get('extra'):
                returnentry['extra'] = {}
            returnentry['extra']['linkedin_url'] = self.linkedin

        return returnentry
        
    def isValidLandscapeItem(self):
        return self.homepage_url and self.logo and self.name

    def invalidLandscapeItemAttributes(self):
        invalidAttributes = []
        if not self.homepage_url:
            invalidAttributes.append('homepage_url')
        if not self.logo:
            invalidAttributes.append('logo')
        if not self.name:
            invalidAttributes.append('name')

        return invalidAttributes

    def overlay(self, membertooverlay: Self, onlykeys: list = [], skipkeys: list = []):
        '''
        Overlay another Member data onto this Member, overriding this Member's values with those 
        from the other Member, and setting other Member's value in this Member if they aren't set
        '''
        for key in dir(membertooverlay):
            if ( onlykeys and key not in onlykeys) or (skipkeys and key in skipkeys):
                continue
            value = getattr(membertooverlay,key,None)
            logging.getLogger().debug("Checking for overlay '{}' - current value '{}' - overlay value '{}'".format(key,getattr(self,key,None),value))
            if isinstance(value,dict):
                for subkey, subvalue in value.items():
                    logging.getLogger().debug("Checking for overlay '{}.{}' - current value '{}' - overlay value '{}'".format(key,subkey,getattr(self,key,{}).get(subkey,'empty'),subvalue))
                    if isinstance(subvalue,dict):
                        for subsubkey, subsubvalue in subvalue.items():
                            logging.getLogger().debug("Checking for overlay '{}.{}.{}' - current value '{}' - overlay value '{}'"
                                    .format(key,subkey,subsubkey,getattr(self,key,{}).get(subkey,{}).get(subsubkey,'empty'),subsubvalue))
                            if subsubvalue != None and getattr(self,key,{}).get(subkey,{}).get(subsubkey,None) != subsubvalue:
                                logging.getLogger().debug("...Overlay '{}.{}.{}'".format(key,subkey,subsubkey))
                                logging.getLogger().debug(".....Old Value - '{}'".format(getattr(self,key,{}).get(subkey,{}).get(subsubkey,'empty')))
                                logging.getLogger().debug(".....New Value - '{}'".format(subsubvalue))
                                if getattr(self,key,{}).get(subkey,False):
                                    getattr(self,key)[subkey][subsubkey] = subsubvalue
                                else:
                                    setattr(self,key,{subkey:{subsubkey:subsubvalue}})
                    elif isinstance(subvalue,list):
                        if subvalue != []:
                            logging.getLogger().debug("...Overlay '{}.{}'".format(key,subkey))
                            logging.getLogger().debug(".....Old Value - '{}'".format(getattr(self,key,{}).get(subkey,[])))
                            logging.getLogger().debug(".....New Value - '{}'".format(self._combine_and_deduplicate(subvalue,getattr(self,key,{}).get(subkey,[]))))
                            if getattr(self,key,False):
                                getattr(self,key)[subkey] = self._combine_and_deduplicate(subvalue,getattr(self,key,{}).get(subkey,[]))
                            else:
                                setattr(self,key,{subkey:self._combine_and_deduplicate(subvalue,getattr(self,key,{}).get(subkey,[]))})
                    else:
                        if subvalue != None and getattr(self,key,{}).get(subkey,None) != subvalue:
                            logging.getLogger().debug("...Overlay '{}.{}'".format(key,subkey))
                            logging.getLogger().debug(".....Old Value - '{}'".format(getattr(self,key,{}).get(subkey,'empty')))
                            logging.getLogger().debug(".....New Value - '{}'".format(subvalue))
                            if getattr(self,key,False):
                                getattr(self,key)[subkey] = subvalue
                            else:
                                setattr(self,key,{subkey:subvalue})
            elif isinstance(value,list):
                if value != []:
                    logging.getLogger().debug("...Overlay '{}'".format(key))
                    logging.getLogger().debug(".....Old Value - '{}'".format(sorted(getattr(self,key,[]))))
                    logging.getLogger().debug(".....New Value - '{}'".format(self._combine_and_deduplicate(value,getattr(self,key,[]))))
                    setattr(self,key,self._combine_and_deduplicate(value,getattr(self,key,[])))
            elif value != None and value != getattr(self,key,None):
                logging.getLogger().debug("...Overlay '{}'".format(key))
                logging.getLogger().debug(".....Old Value - '{}'".format(getattr(self,key,None)))
                logging.getLogger().debug(".....New Value - '{}'".format(value))
                setattr(self,key,value)


    def _combine_and_deduplicate(self, list1, list2):
        """Combines two lists (potentially containing dictionaries) and removes duplicates."""

        # Convert dictionaries to tuples for hashing
        def to_hashable(item):
            if isinstance(item, dict):
                return tuple(sorted(item.items()))
            return item

        # Combine lists and remove duplicates
        combined = list1 + list2
        seen = set()
        result = []
        for item in combined:
            hashable_item = to_hashable(item)
            if hashable_item not in seen:
                seen.add(hashable_item)
                result.append(item)

        return result
