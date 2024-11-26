#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

import unittest
import tempfile
import responses
import requests
import logging
import json

from lfx_landscape_tools.config import Config
from lfx_landscape_tools.cli import Cli
from lfx_landscape_tools.member import Member
from lfx_landscape_tools.members import Members
from lfx_landscape_tools.lfxmembers import LFXMembers
from lfx_landscape_tools.landscapemembers import LandscapeMembers
from lfx_landscape_tools.landscapeoutput import LandscapeOutput
from lfx_landscape_tools.svglogo import SVGLogo
from lfx_landscape_tools.lfxprojects import LFXProjects
from lfx_landscape_tools.tacagendaproject import TACAgendaProject

class TestSVGLogo(unittest.TestCase):
    def testPassInContents(self):
        self.assertEqual(str(SVGLogo(contents="This is a test")),"This is a test")

    def testCreateTextLogo(self):
        self.maxDiff = None
        self.assertIn('<?xml version="1.0" encoding="UTF-8"?>',str(SVGLogo(name="This is a test")))

    @responses.activate
    def testHostLogo(self):
        responses.add(
            method=responses.GET,
            url='https://someurl.com/boom.svg',
            body='this is image data'
            )

        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            self.assertEqual(str(SVGLogo(url="https://someurl.com/boom.svg")),"this is image data")

    @responses.activate
    def testHostLogoFileNameUnicode(self):
        responses.add(
            method=responses.GET,
            url='https://someurl.com/boom.svg',
            body='this is image data'
            )

        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            self.assertEqual(str(SVGLogo(url="https://someurl.com/boom.svg").filename('privée')),'privee.svg')
    
    @responses.activate
    def testHostLogoNonASCII(self):
        responses.add(
            method=responses.GET,
            url='https://someurl.com/boom.svg',
            body=b'this is image data'
            )

        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            self.assertEqual(str(SVGLogo(url="https://someurl.com/boom.svg").filename('北京数悦铭金技术有限公司')),'bei_jing_shu_yue_ming_jin_ji_zhu_you_xian_gong_si.svg')
        
    def testHostLogoContainsPNG(self):
        self.assertFalse(SVGLogo(contents="this is image data data:image/png;base64 dfdfdf").isValid())

    @responses.activate
    def testHostLogoContainsText(self):
        self.assertFalse(SVGLogo(contents="this is image data <text /> dfdfdf").isValid())
    
    @responses.activate(registry=responses.registries.OrderedRegistry)
    def testHostLogoRetriesOnChunkedEncodingErrorException(self):
        responses.add(
            method=responses.GET,
            url='https://someurl.com/boom.svg',
            body=requests.exceptions.ChunkedEncodingError("Connection broken: IncompleteRead(55849 bytes read, 19919 more expected)")
        )
        responses.add(
            method=responses.GET,
            url='https://someurl.com/boom.svg',
            body=b'this is image data'
            )

        self.assertEqual(str(SVGLogo(url="https://someurl.com/boom.svg")),"this is image data")

    def testHostLogoLogoisNone(self):
        self.assertEqual(str(SVGLogo()),'')

    @responses.activate
    def testHostLogoUnicodeError(self):
        responses.add(
            method=responses.GET,
            url='https://someurl.com/boom.jpg',
            body=UnicodeDecodeError('funnycodec', b'\x00\x00', 1, 2, 'This is just a fake reason!')
            )
        
        self.assertEqual(str(SVGLogo(url="https://someurl.com/boom.jpg")),"")

    @responses.activate
    def testHostLogo404(self):
        responses.add(
            method=responses.GET,
            url='https://someurl.com/boom.svg',
            body='{"error": "not found"}', status=404,
        )

        self.assertEqual(str(SVGLogo(url="https://someurl.com/boom.svg")),"")

    @responses.activate
    def testSaveLogo(self):
        with tempfile.TemporaryDirectory() as tempdir:
            self.assertEqual(SVGLogo(contents="this is a file").save('dog',tempdir),'dog.svg')
    
    @responses.activate
    def testAutocropLogo(self):
        responses.add(
            method=responses.POST,
            url='https://autocrop.cncf.io/autocrop',
            body=json.dumps({"success": True, "result": "this is a file"})
        )

        logo = SVGLogo(contents="this is a dog")
        logo.autocrop()
        self.assertEqual(str(logo),'this is a file')

    @responses.activate
    def testAutocropLogoFail(self):
        responses.add(
            method=responses.POST,
            url='https://autocrop.cncf.io/autocrop',
            body=json.dumps({"success": False, "error": "this is a file"})
        )

        with self.assertRaises(RuntimeError) as cm:
            logo = SVGLogo(contents="this is a dog")
            logo.autocrop()
        
        self.assertEqual(str(cm.exception),'Autocrop failed: this is a file')
    
    @responses.activate
    def testCaptionLogo(self):
        responses.add(
            method=responses.POST,
            url='https://autocrop.cncf.io/autocrop',
            body=json.dumps({"success": True, "result": "this is a file"})
        )

        logo = SVGLogo(contents="this is a dog")
        logo.addCaption("Dog")
        self.assertEqual(str(logo),'this is a file')

    @responses.activate
    def testCaptionLogoFail(self):
        responses.add(
            method=responses.POST,
            url='https://autocrop.cncf.io/autocrop',
            body=json.dumps({"success": False, "error": "this is a file"})
        )

        with self.assertRaises(RuntimeError) as cm:
            logo = SVGLogo(contents="this is a dog")
            logo.addCaption("Dog")
        
        self.assertEqual(str(cm.exception),'Adding caption failed: this is a file')

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("debug.log"),
        ]
    )
    
    unittest.main()
