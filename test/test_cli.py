#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import argparse
from datetime import datetime
import logging

from lfx_landscape_tools.cli import Cli

class TestCli(unittest.TestCase):

    def setUp(self):
        """Mock external dependencies to prevent network/file IO during tests."""
        # Mocking the heavy-lifter classes
        self.patch_config = patch('lfx_landscape_tools.cli.Config')
        self.patch_output = patch('lfx_landscape_tools.cli.LandscapeOutput')
        self.patch_members = patch('lfx_landscape_tools.cli.LFXMembers')
        self.patch_projects = patch('lfx_landscape_tools.cli.LFXProjects')
        self.patch_svg = patch('lfx_landscape_tools.cli.SVGLogo')
        self.patch_run = patch('lfx_landscape_tools.cli.subprocess.run')

        self.mock_config = self.patch_config.start()
        self.mock_output = self.patch_output.start()
        self.mock_members = self.patch_members.start()
        self.mock_projects = self.patch_projects.start()
        self.mock_svg = self.patch_svg.start()
        self.mock_run = self.patch_run.start()

        self.patch_file = patch('argparse.FileType', return_value=lambda x: mock_open(read_data="dummy").return_value)
        self.patch_file.start()

    def tearDown(self):
        """Clean up mocks."""
        patch.stopall()

    @patch('sys.argv', ['cli.py', '--silent', 'build_members'])
    def test_build_members_routing(self):
        """Verify build_members command triggers the LFXMembers pipeline."""
        Cli()
        # Ensure LFXMembers was initialized
        self.mock_members.assert_called()
        # Ensure LandscapeOutput was loaded and saved
        self.mock_output.return_value.load.assert_called_once()
        self.mock_output.return_value.save.assert_called_once()

    @patch('sys.argv', ['cli.py', 'maketextlogo', '--name', 'OpenSource', '-o', 'logo.svg'])
    def test_maketextlogo_args(self):
        """Verify logo command correctly passes arguments to SVGLogo."""
        Cli()
        self.mock_svg.assert_called_with(name='OpenSource')
        self.mock_svg.return_value.save.assert_called_with('logo.svg')

    @patch('sys.argv', ['cli.py', '--silent', 'validatedata', 'test.yml'])
    def test_validatedata_subprocess(self):
        """Verify the JSON schema validator command is constructed properly."""
        Cli()
        # Check if subprocess.run was called with the check-jsonschema command
        call_args = self.mock_run.call_args[0][0]
        self.assertIn("check-jsonschema", call_args)
        self.assertIn("test.yml", call_args)

    @patch('sys.argv', ['cli.py', '--verbose', 'sync_projects'])
    @patch('logging.basicConfig')
    def test_verbose_flag_sets_info_level(self, mock_log_config):
        """Verify that --verbose overrides the default log level to INFO."""
        Cli()
        # logging.INFO constant value is 20
        _, kwargs = mock_log_config.call_args
        self.assertEqual(kwargs['level'], logging.INFO)

    def test_dir_path_validation(self):
        """Test the directory validation helper logic directly."""
        # Create instance without running __init__ to test helper method in isolation
        cli_manual = Cli.__new__(Cli)

        with patch('os.path.isdir', return_value=True):
            self.assertEqual(cli_manual._dir_path("/tmp"), "/tmp")

        with patch('os.path.isdir', return_value=False):
            with self.assertRaises(argparse.ArgumentTypeError):
                cli_manual._dir_path("/non/existent/path")

    @patch('sys.argv', ['cli.py', '--log', 'debug', 'build_members'])
    @patch('lfx_landscape_tools.cli.LFXMembers', side_effect=Exception("Critical Failure"))
    @patch('argparse.ArgumentParser.print_help')
    def test_error_handling_prints_help(self, mock_help, _):
        """Ensure that if a command fails, the help message is displayed."""
        Cli()
        mock_help.assert_called_once()

if __name__ == '__main__':
    unittest.main()
