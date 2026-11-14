#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8
"""
Shared setup for the fuzz harnesses.

The harnesses must run without network access and without touching the
local filesystem, so this module replaces every code path in the package
that would make an HTTP request or open an arbitrary file with a stub.
"""

import logging

import requests

# Quiet the package's logging: it logs on almost every input and would
# otherwise dominate fuzzing time and output.
logging.disable(logging.CRITICAL)

# Mirrors the landscape2 item schema that Member normally downloads from
# https://raw.githubusercontent.com/cncf/landscape2/refs/heads/main/docs/config/data.yml
_EXTRA_KEYS = [
    'accepted', 'archived', 'audits', 'annual_review_date', 'annual_review_url',
    'artwork_url', 'blog_url', 'bluesky_url', 'chat_channel', 'clomonitor_name',
    'dev_stats_url', 'discord_url', 'docker_url', 'documentation_url',
    'facebook_url', 'github_discussions_url', 'gitter_url', 'graduated',
    'incubating', 'lfx_slug', 'linkedin_url', 'mailing_list_url', 'other_links',
    'package_manager_url', 'parent_project', 'pinterest_url', 'reddit_url',
    'slack_url', 'specification', 'stack_overflow_url',
    'summary_business_use_case', 'summary_integration', 'summary_integrations',
    'summary_intro_url', 'summary_personas', 'summary_release_rate',
    'summary_tags', 'summary_use_case', 'tag', 'youtube_url',
]

ITEM_SCHEMA = {
    'name': None, 'homepage_url': None, 'logo': None, 'description': None,
    'second_path': None, 'project': None, 'joined': None, 'repo_url': None,
    'branch': None, 'license': None, 'additional_repos': None,
    'crunchbase': None, 'twitter': None, 'url_for_bestpractices': None,
    'enduser': None,
    'extra': {**{k: None for k in _EXTRA_KEYS}, 'annotations': {'key1': None, 'key2': None}},
}


class _NoNetworkSession:
    """Stands in for requests_cache.CachedSession; every request fails."""

    def __init__(self, *args, **kwargs):
        pass

    def get(self, *args, **kwargs):
        raise requests.exceptions.ConnectionError("network disabled while fuzzing")


def install():
    """Patch out network and file access. Call before running any input."""
    from lfx_landscape_tools import member as member_module
    from lfx_landscape_tools.member import Member
    from lfx_landscape_tools.svglogo import SVGLogo

    member_module.requests_cache.CachedSession = _NoNetworkSession
    Member.itemschema = ITEM_SCHEMA

    # GitHub lookups: pretend the org has no pinned or public repos.
    Member._get_pinned_github_repos_from_github_org = lambda self, url: []
    Member._get_primary_github_repo_from_github_org = lambda self, url: None

    # Logos given as URLs or file paths load nothing.
    SVGLogo._load_from_url = lambda self, url: None
    SVGLogo._load_from_file = lambda self, filename: None
