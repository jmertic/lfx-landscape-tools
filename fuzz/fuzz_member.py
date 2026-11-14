#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8
"""
Fuzz Member's normalizing property setters (name, homepage_url, repo_url,
crunchbase, linkedin, twitter, logo, extra), then convert the member into
a landscape item and overlay it onto a second member.

These setters clean up URLs and fields that come straight from the LFX API
and from landscape.yml, so they should never raise on odd input.
"""

import sys

import atheris

with atheris.instrument_imports():
    from lfx_landscape_tools.member import Member

import offline

STRING_FIELDS = ['name', 'homepage_url', 'repo_url', 'crunchbase', 'linkedin', 'twitter', 'logo']

# Prefixes that steer inputs into each setter's URL-handling branches.
URL_PREFIXES = [
    '', 'https://', 'http://', 'https://github.com/', 'https://www.github.com/',
    'github.com/', 'https://crunchbase.com/', 'https://www.crunchbase.com/organization/',
    'company/', 'linkedin.com/', 'www.linkedin.com/', 'https://www.linkedin.com/',
    'https://twitter.com/', 'https://www.twitter.com/',
]

EXTRA_KEYS = list(offline.ITEM_SCHEMA['extra'].keys()) + ['unknown_key']

MAX_STRING_LENGTH = 128


def _consume_string(fdp):
    if fdp.ConsumeIntInRange(0, 9) == 0:
        return None
    prefix = fdp.PickValueInList(URL_PREFIXES)
    return prefix + fdp.ConsumeUnicodeNoSurrogates(MAX_STRING_LENGTH)


def _consume_extra(fdp):
    extra = {}
    for _ in range(fdp.ConsumeIntInRange(0, 5)):
        key = fdp.PickValueInList(EXTRA_KEYS)
        if key == 'other_links':
            extra[key] = [
                {'name': _consume_string(fdp), 'url': _consume_string(fdp)}
                for _ in range(fdp.ConsumeIntInRange(0, 3))
            ]
        elif key == 'annotations':
            extra[key] = {_consume_string(fdp) or 'k': _consume_string(fdp)}
        else:
            extra[key] = _consume_string(fdp)
    return extra


def _consume_member(fdp):
    member = Member()
    for field in STRING_FIELDS:
        setattr(member, field, _consume_string(fdp))
    member.extra = _consume_extra(fdp)
    return member


def TestOneInput(data: bytes):
    fdp = atheris.FuzzedDataProvider(data)
    member = _consume_member(fdp)

    member.to_landscape_item_attributes()
    member.is_valid_landscape_item()
    member.invalid_landscape_item_attributes()

    other = _consume_member(fdp)
    other.overlay(member)
    other.to_landscape_item_attributes()


def main():
    offline.install()
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
