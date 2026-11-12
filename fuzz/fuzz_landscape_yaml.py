#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8
"""
Fuzz LandscapeMembers loading a landscape.yml file: YAML parsing, walking
the categories/subcategories/items tree, and building Member objects from
each item.
"""

import os
import sys
import tempfile

import atheris

with atheris.instrument_imports():
    from lfx_landscape_tools.config import Config
    from lfx_landscape_tools.landscapemembers import LandscapeMembers

import offline

WORKDIR = tempfile.mkdtemp(prefix='fuzz_landscape_')
LANDSCAPE_FILE = 'landscape.yml'

# Seed the fuzzer with a valid prefix so it spends its time past the YAML
# parser, inside the landscape-walking code.
SKELETON = (
    "landscape:\n"
    "  - name: Members\n"
    "    subcategories:\n"
    "      - name: Premier\n"
    "        items:\n"
)


def _config():
    config = Config()
    config.basedir = WORKDIR
    config.landscapefile = LANDSCAPE_FILE
    return config


def TestOneInput(data: bytes):
    fdp = atheris.FuzzedDataProvider(data)
    use_skeleton = fdp.ConsumeBool()
    body = fdp.ConsumeUnicodeNoSurrogates(fdp.remaining_bytes())
    contents = SKELETON + body if use_skeleton else body

    with open(os.path.join(WORKDIR, LANDSCAPE_FILE), 'w', encoding='utf-8') as f:
        f.write(contents)

    LandscapeMembers(_config())


def main():
    offline.install()
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
