#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8
"""
Fuzz SVGLogo generation from a name (SVGLogo(name=...)), which renders
member and project names from LFX into a placeholder SVG with cairo, and
the filename derived from that name.
"""

import sys

import atheris

with atheris.instrument_imports():
    from lfx_landscape_tools.svglogo import SVGLogo

# Real names are short; cap the length so cairo rendering stays fast.
MAX_NAME_LENGTH = 256


def TestOneInput(data: bytes):
    fdp = atheris.FuzzedDataProvider(data)
    name = fdp.ConsumeUnicodeNoSurrogates(MAX_NAME_LENGTH)
    logo = SVGLogo(name=name)
    str(logo)
    logo.filename(name)


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
