#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

import unittest
from unittest.mock import patch, mock_open, MagicMock
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

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("debug.log",mode="w"),
        ]
    )

    def setUp(self):
        logging.getLogger().debug("Running {}".format(unittest.TestCase.id(self)))

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

        with unittest.mock.patch("lfx_landscape_tools.svglogo.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            self.assertEqual(str(SVGLogo(url="https://someurl.com/boom.svg")),"this is image data")

    @responses.activate
    def testHostLogoFileNameUnicode(self):
        responses.add(
            method=responses.GET,
            url='https://someurl.com/boom.svg',
            body='this is image data'
            )

        with unittest.mock.patch("lfx_landscape_tools.svglogo.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            self.assertEqual(str(SVGLogo(url="https://someurl.com/boom.svg").filename('privée')),'privee.svg')

    @responses.activate
    def testHostLogoNonASCII(self):
        responses.add(
            method=responses.GET,
            url='https://someurl.com/boom.svg',
            body=b'this is image data'
            )

        with unittest.mock.patch("lfx_landscape_tools.svglogo.open", unittest.mock.mock_open(read_data="data")) as mock_file:
            self.assertEqual(str(SVGLogo(url="https://someurl.com/boom.svg").filename('北京数悦铭金技术有限公司')),'bei_jing_shu_yue_ming_jin_ji_zhu_you_xian_gong_si.svg')

    def testHostLogoContainsPNG(self):
        self.assertFalse(SVGLogo(contents="this is image data data:image/png;base64 dfdfdf").isValid())

    @patch('builtins.open', new_callable=mock_open, read_data="svg_content_here")
    @patch('lfx_landscape_tools.svglogo.logging.getLogger')
    def test_load_from_file_success(self, mock_get_logger, mock_file):
        """Test successful file loading and attribute setting."""
        logo = SVGLogo.__new__(SVGLogo)
        test_path = "/path/to/my_logo.svg"

        logo._load_from_file(test_path)

        self.assertEqual(logo._SVGLogo__contents, "svg_content_here")
        self.assertEqual(logo._SVGLogo__filename, "my_logo.svg")

        mock_get_logger.return_value.debug.assert_called_with("Filename loaded 'my_logo.svg'")
        mock_file.assert_called_once_with(test_path, 'r')

    @patch('builtins.open', side_effect=FileNotFoundError)
    @patch('lfx_landscape_tools.svglogo.logging.getLogger')
    def test_load_from_file_not_found(self, mock_get_logger, mock_file):
        """Test behavior when the file does not exist."""
        logo = SVGLogo.__new__(SVGLogo)
        test_path = "non_existent.svg"

        logo._load_from_file(test_path)

        mock_get_logger.return_value.warning.assert_called_with(f"Logo '{test_path}' not found")

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

    @patch('os.path.isdir')
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_creates_directory_if_missing(self, mock_file, mock_makedirs, mock_isdir):
        """Test path 1: Directory doesn't exist, must be created."""
        # Setup
        logo = SVGLogo.__new__(SVGLogo)
        logo._SVGLogo__contents = "<svg>data</svg>"
        mock_isdir.return_value = False # Force the 'if' block to trigger

        # Execute
        result = logo.save("test_logo", path="./new_folder")

        # Verify
        mock_isdir.assert_called_with("./new_folder")
        mock_makedirs.assert_called_once_with("./new_folder")
        mock_file.assert_called_once()
        self.assertEqual(result, logo.filename("test_logo"))

    @patch('os.path.isdir')
    @patch('builtins.open', side_effect=FileNotFoundError)
    @patch('logging.getLogger')
    def test_save_handles_file_not_found_error(self, mock_get_logger, mock_file, mock_isdir):
        """Test path 2: Directory exists, but saving fails (FileNotFoundError)."""
        # Setup
        logo = SVGLogo.__new__(SVGLogo)
        logo._SVGLogo__contents = "data"
        mock_isdir.return_value = True # Skip makedirs

        # Execute
        logo.save("test_logo", path="./readonly_dir")

        # Verify
        mock_get_logger.return_value.error.assert_called_with(
            "Cannot save 'test_logo.svg' in './readonly_dir'"
        )
