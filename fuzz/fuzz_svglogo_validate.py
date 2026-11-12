#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8
"""
Fuzz SVGLogo.is_valid(), which parses logo SVGs fetched from LFX and
member websites with xml.etree.ElementTree.

is_valid() must return True or False for any input and never raise.
"""

import sys

import atheris

with atheris.instrument_imports():
    from lfx_landscape_tools.svglogo import SVGLogo


def TestOneInput(data: bytes):
    contents = data.decode('utf-8', errors='replace')
    result = SVGLogo(contents=contents).is_valid()
    if not isinstance(result, bool):
        raise TypeError(f"is_valid() returned {type(result).__name__}, expected bool")


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
