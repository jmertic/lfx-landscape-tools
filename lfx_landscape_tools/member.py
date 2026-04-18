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
import time

## third party modules
from url_normalize import url_normalize
import validators
import requests
import requests_cache
from github import Github, GithubException, RateLimitExceededException, Auth, UnknownObjectException
import ruamel.yaml
from bs4 import BeautifulSoup

from lfx_landscape_tools.svglogo import SVGLogo

#
# Member object to ensure we have normalization on fields. Only fields that are required or need validation are defined; others can be added dynamically.
#
class Member:

    membership = None
    project = None
    project_org = None
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
        # Per-instance containers for mutable fields. Declaring these at
        # class level would alias a single dict/list across every Member
        # instance, causing values written to one member to surface on
        # others (see sync_members leak symptoms).
        self.second_path = []
        self.__extra = {}
        self.additional_repos = []

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
            self.itemschema = dataschema.get('categories',[])[0].get('subcategories',[])[0].get('items',[])[0]

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

    def _fetch_best_repo_via_api(self, org_name):
        """Extracted helper to handle GitHub API search and rate limiting."""
        token = os.environ.get('GITHUB_TOKEN')
        auth = token and Auth.Token(token)
        g = Github(auth=auth, per_page=1000)

        while True:
            try:
                query = f"org:{org_name}"
                repos = g.search_repositories(query=query, sort="stars", order="desc")

                # Use next() for efficiency instead of converting whole result to a list
                first_repo = next(iter(repos), None)
                return first_repo.html_url if first_repo else ''
            except UnknownObjectException:
                logging.debug(f"Organization or Repository not found: {org_name}")
                return False
            except RateLimitExceededException:
                sleep_time = g.rate_limiting_resettime - int(time.time())
                logging.info(f"Rate limit hit. Sleeping for {sleep_time} seconds...")
                time.sleep(max(sleep_time, 1))
            except GithubException as e:
                if e.status == 502:
                    logging.debug("Server error (502) - retrying...")
                    continue
                logging.getLogger().warning(e.data)
                return None
            except (socket.timeout, ConnectionError):
                logging.debug("Network error - retrying...")
                continue

    def _getPrimaryGitHubRepoFromGitHubOrg(self, url):
        if not self._isGitHubOrg(url):
            return url # Removed list(url) as it likely intended to return the string

        pinned = self._getPinnedGithubReposFromGithubOrg(url)
        if pinned:
            return pinned[0]

        org_name = urlparse(url).path.split("/")[1]
        with requests_cache.enabled():
            return self._fetch_best_repo_via_api(org_name)

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
            logging.getLogger().warning(f"Member.logo must be not be blank for '{self.name}'")
            return
        elif type(logo) is SVGLogo:
            self.__logo = logo
        elif urlparse(logo).scheme != '':
            self.__logo = SVGLogo(url=logo)
        else:
            self.__logo = SVGLogo(filename=logo)

        if not self.__logo.isValid():
            self.__logo = None
            logging.getLogger().warning(f"Member.logo for '{self.name}' invalid format")

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

    def _sanitize_links(self, links):
        """Helper to filter valid name/url pairs from other_links."""
        if not isinstance(links, list):
            return []
        return [
            link for link in links
            if link.get('name') and validators.url(str(link.get('url', '')))
        ]

    @extra.setter
    def extra(self, extra):
        logger = logging.getLogger()

        # Guard Clause: Early exit for invalid types
        if not isinstance(extra, dict):
            logger.debug(f"Member.extra for '{self.name}' must be a dict - '{extra}' provided")
            self.__extra = {}
            return

        endextra = {}
        endannotations = {}

        for key, value in extra.items():
            # 1. Handle special 'other_links' case
            if key == 'other_links':
                endextra['other_links'] = self._sanitize_links(value)
                continue

            # 2. Skip empty/nil values
            if not value or value == 'nil':
                logger.debug(f"Removing Member.extra.{key} for '{self.name}' (value: '{value}')")
                continue

            # 3. Categorize as Annotation or Extra
            if key not in self.itemschema.get('extra',[]):
                logger.debug(f"Moving Member.extra.{key} for '{self.name}' under 'annotations'")
                endannotations[key] = value
            else:
                endextra[key] = value

        # Merge annotations and filter out None values
        merged_annotations = endextra.get('annotations', {}) | endannotations
        endextra['annotations'] = {k: v for k, v in merged_annotations.items() if v is not None}

        self.__extra = endextra

    def _get_nested_attr(self, key, subkey=None, subsubkey=None):
        """Helper to safely fetch nested attributes from the object."""
        data = getattr(self, key, {})
        if not data or not isinstance(data, dict):
            return None

        val = data.get(subkey)
        if subsubkey and isinstance(val, dict):
            return val.get(subsubkey)
        return val

    def _map_schema_item(self, key, value):
        """Maps a single top-level schema key to its value."""
        if key == 'name':
            return f"{self.name}{self.entrysuffix}"
        if key == 'logo' and isinstance(self.__logo, SVGLogo):
            return self.__logo.filename(self.name)

        attr_val = getattr(self, key, None)
        if not attr_val:
            return None

        # Handle nested dictionary mapping (Recursion or Helpers)
        if isinstance(value, dict):
            return self._build_nested_attributes(key, value)

        return attr_val

    def _build_nested_attributes(self, key, schema_dict):
        """Handles the nested dictionary logic (previously 3 loops deep)."""
        result = {}
        for subkey, subvalue in schema_dict.items():
            val = self._get_nested_attr(key, subkey)
            if not val:
                continue

            # Handle 3rd level depth (subsubkeys)
            if isinstance(subvalue, dict) and subkey != 'annotations':
                sub_result = {ss_k: self._get_nested_attr(key, subkey, ss_k)
                             for ss_k in subvalue.keys()
                             if self._get_nested_attr(key, subkey, ss_k)}
                if sub_result:
                    result[subkey] = sub_result
            else:
                result[subkey] = val
        return result or None

    def toLandscapeItemAttributes(self):
        """Converts the member object attributes into the format that would go into the landscape file entry."""
        logging.getLogger().debug("Processing into landscape item attributes")

        returnentry = {k: self._map_schema_item(k, v) for k, v in self.itemschema.items()}
        returnentry = {'item': None} | {k: v for k, v in returnentry.items() if v is not None}

        if self.project_org:
            pinned = self._getPinnedGithubReposFromGithubOrg(self.project_org)
            returnentry['additional_repos'] = [{'repo_url': u} for u in pinned if u != self.repo_url]
            # Use a helper to set deep extra.annotations
            self._set_extra_annotation(returnentry, 'project_org', self.project_org)

        if self.linkedin:
            self._set_extra_field(returnentry, 'linkedin_url', self.linkedin)

        return returnentry

    def _set_extra_annotation(self, entry, key, value):
        """Helper to handle the messy dictionary nesting for annotations."""
        extra = entry.setdefault('extra', {})
        annotations = extra.setdefault('annotations', {})
        annotations[key] = value

    def _set_extra_field(self, entry, key, value):
        """Helper to set a field directly in the extra dict."""
        extra = entry.setdefault('extra', {})
        extra[key] = value

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

    def _update_nested_dict(self, attr_key, current_dict, overlay_dict):
        """Helper to handle the deep dictionary and list logging/merging."""
        logger = logging.getLogger()
        for skey, sval in overlay_dict.items():
            curr_sval = current_dict.get(skey, 'empty')
            logger.debug(f"Checking for overlay '{attr_key}.{skey}' - current '{curr_sval}' - overlay '{sval}'")

            if isinstance(sval, dict):
                # Handle 3rd level depth
                sub_dict = current_dict.setdefault(skey, {})
                for s_skey, s_sval in sval.items():
                    curr_ssval = sub_dict.get(s_skey, 'empty')
                    logger.debug(f"Checking for overlay '{attr_key}.{skey}.{s_skey}' - current '{curr_ssval}' - overlay '{s_sval}'")
                    if s_sval is not None and curr_ssval != s_sval:
                        logger.debug(f"...Overlay '{attr_key}.{skey}.{s_skey}'\n.....Old: '{curr_ssval}'\n.....New: '{s_sval}'")
                        sub_dict[s_skey] = s_sval
            elif isinstance(sval, list):
                new_list = self._combine_and_deduplicate(sval, current_dict.get(skey, []))
                logger.debug(f"...Overlay '{attr_key}.{skey}'\n.....Old: '{current_dict.get(skey, [])}'\n.....New: '{new_list}'")
                current_dict[skey] = new_list
            elif sval is not None and curr_sval != sval:
                logger.debug(sval)
                logger.debug(f"...Overlay '{attr_key}.{skey}'\n.....Old: '{curr_sval}'\n.....New: '{sval}'")
                current_dict[skey] = sval

    def overlay(self, membertooverlay: 'Member', onlykeys: list = [], skipkeys: list = []):
        '''
        Overlay another Member data onto this Member, overriding this Member's values with those
        from the other Member, and setting other Member's value in this Member if they aren't set
        '''
        logger = logging.getLogger()
        for key in dir(membertooverlay):
            if key.startswith('__') or (onlykeys and key not in onlykeys) or (skipkeys and key in skipkeys):
                continue

            val = getattr(membertooverlay, key, None)
            curr = getattr(self, key, None)
            logger.debug(f"Checking for overlay '{key}' - current '{curr}' - overlay '{val}'")

            if isinstance(val, dict):
                base = curr if isinstance(curr, dict) else {}
                self._update_nested_dict(key, base, val)
                setattr(self, key, base)
            elif isinstance(val, list):
                logger.debug(f"...Overlay '{key}'\n.....Old: '{sorted(getattr(self, key, []), key=lambda x: str(x))}'")
                new_list = self._combine_and_deduplicate(val, getattr(self, key, []))
                logger.debug(f".....New: '{new_list}'")
                setattr(self, key, new_list)
            elif val is not None and val != curr:
                logger.debug(f"...Overlay '{key}'\n.....Old: '{curr}'\n.....New: '{val}'")
                setattr(self, key, val)

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
