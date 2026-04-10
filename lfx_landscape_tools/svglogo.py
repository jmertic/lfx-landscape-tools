#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

## built in modules
import os
import tempfile
from pathlib import Path
from slugify import slugify
from typing import Self
import logging

## third party modules
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import cairo

class SVGLogo:

    __contents = ''
    __filename = None

    def __init__(self, contents=None, filename=None, url=None, name=None):
        self.__contents = ''
        self.__filename = None

        if contents:
            self.__contents = contents
        elif filename:
            self._load_from_file(filename)
        elif url:
            self._load_from_url(url)
        elif name:
            self._generate_from_name(name)

    def _load_from_file(self, filename):
        """Helper to handle file IO complexity."""
        try:
            with open(filename, 'r') as f:
                self.__contents = f.read()
                self.__filename = os.path.basename(filename)
                logging.getLogger().debug(f"Filename loaded '{self.__filename}'")
        except FileNotFoundError:
            logging.getLogger().warning(f"Logo '{filename}' not found")

    def _load_from_url(self, url):
        """Helper to handle HTTP request and retry complexity."""
        session = requests.Session()
        session.mount('http://', HTTPAdapter(max_retries=Retry(backoff_factor=0.5)))
        session.mount('https://', HTTPAdapter(max_retries=Retry(backoff_factor=0.5)))

        while True:
            try:
                r = session.get(url, allow_redirects=True, timeout=10)
                if r.status_code == 200:
                    self.__contents = r.content.decode('utf-8')
                    logging.getLogger().debug(f"URL loaded '{url}'")
                break
            except requests.exceptions.ChunkedEncodingError:
                pass
            except (requests.exceptions.RequestException, UnicodeDecodeError) as e:
                logging.getLogger().warning(f"Failed to load logo from URL '{url}': {e}")
                break

    def _generate_from_name(self, name):
        """Helper to handle Cairo SVG generation complexity."""
        parts = name.split(" ")
        width = len(max(parts, key=len)) * 34
        height = len(parts) * 65

        with tempfile.TemporaryFile() as fp:
            with cairo.SVGSurface(fp, width, height) as surface:
                ctx = cairo.Context(surface)
                ctx.set_source_rgb(0, 0, 0)
                ctx.set_font_size(60)
                ctx.select_font_face("cairo:monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)

                for n, part in enumerate(parts, start=1):
                    ctx.move_to(0, n * 50)
                    ctx.show_text(part)

                ctx.stroke()
                ctx.save()
            fp.seek(0)
            logging.getLogger().debug(f"Generated logo from name {name}")
            self.__contents = fp.read().decode('utf-8')

    def __str__(self):
        return str(self.__contents or '')

    def filename(self, name):
        return self.__filename if self.__filename else "{}.svg".format(slugify(os.path.splitext(name)[0],separator='_'))

    def save(self, name, path = './'):
        filename = self.filename(name)
        filenamepath = os.path.normpath("{}/{}".format(path,filename))
        if not os.path.isdir(path):
            os.makedirs(path)

        try:
            with open(filenamepath, 'w') as fp:
                logging.getLogger().debug("Saving hosted_logos '{}'".format(filenamepath))
                fp.write(self.__contents)
        except FileNotFoundError:
            logging.getLogger().error("Cannot save '{}' in '{}'".format(filename,path))

        return filename

    def isValid(self):
        return self.__contents != '' and self.__contents.find('base64') == -1 and self.__contents.find('<text') == -1 and self.__contents.find('<image') == -1 and self.__contents.find('<tspan') == -1

    def addCaption(self, caption="", title=""):
        postJson = {
            'svg': self.__contents,
            'title': title,
            'caption': caption
        }
        x = requests.post("https://autocrop.cncf.io/autocrop", json=postJson)
        response = x.json()
        if response['success']:
            self.__contents = response['result']
        else:
            raise RuntimeError("Adding caption failed: {}".format(response['error']))

    def autocrop(self, title=''):
        postJson = {
            'svg': self.__contents,
            'title': title
        }
        x = requests.post("https://autocrop.cncf.io/autocrop", json=postJson)
        response = x.json()
        if response['success']:
            self.__contents = response['result']
        else:
            raise RuntimeError("Autocrop failed: {}".format(response['error']))
