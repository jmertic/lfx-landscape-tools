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
from pathlib import Path
import tempfile
from types import SimpleNamespace
import os

from lfx_landscape_tools.cli import Cli
from lfx_landscape_tools.svglogo import SVGLogo


class TestCli(unittest.TestCase):

    def setUp(self):
        """Mock external dependencies to prevent network/file IO during tests."""
        # Mocking the heavy-lifter classes
        self.patch_config = patch('lfx_landscape_tools.cli.Config')
        self.patch_output = patch('lfx_landscape_tools.cli.LandscapeOutput')
        self.patch_members = patch('lfx_landscape_tools.cli.LFXMembers')
        self.patch_projects = patch('lfx_landscape_tools.cli.LFXProjects')
        self.patch_lfeuprojects = patch('lfx_landscape_tools.cli.LFXProjectsEU')
        self.patch_svg = patch('lfx_landscape_tools.cli.SVGLogo')
        self.patch_run = patch('lfx_landscape_tools.cli.subprocess.run')
        self.patch_tacagendaproject = patch('lfx_landscape_tools.cli.TACAgendaProject')
        self.patch_landscapemembers = patch('lfx_landscape_tools.cli.LandscapeMembers')

        self.mock_config = self.patch_config.start()
        self.mock_output = self.patch_output.start()
        self.mock_members = self.patch_members.start()
        self.mock_projects = self.patch_projects.start()
        self.mock_lfeuprojects = self.patch_lfeuprojects.start()
        self.mock_svg = self.patch_svg.start()
        self.mock_run = self.patch_run.start()
        self.mock_tacagendaproject = self.patch_tacagendaproject.start()
        self.mock_landscapemembers = self.patch_landscapemembers.start()

        self.patch_file = patch('argparse.FileType', return_value=lambda x: mock_open(read_data="dummy").return_value)
        self.patch_file.start()

    def tearDown(self):
        """Clean up mocks."""
        patch.stopall()

    @patch('sys.argv', ['cli.py', '--silent', 'build_members'])
    @patch('builtins.open', new_callable=mock_open, read_data="--- \n # valid yaml content")
    def test_build_members_routing(self, mock_file):
        """Verify build_members command triggers the LFXMembers pipeline."""
        Cli()
        self.mock_members.assert_called()
        self.mock_output.return_value.load.assert_called_once()
        self.mock_output.return_value.save.assert_called_once()

    @patch('sys.argv', ['cli.py', '--silent', 'build_lfeuprojects'])
    @patch('builtins.open', new_callable=mock_open, read_data="--- \n # valid yaml content")
    def test_build_lfeuprojects_routing(self, mock_file):
        """Verify build_lfeuprojects command triggers the LFXProjectsEU pipeline."""
        Cli()
        self.mock_lfeuprojects.assert_called()
        self.mock_output.return_value.load.assert_called_once()
        self.mock_output.return_value.save.assert_called_once()

    @patch('sys.argv', ['cli.py', '--silent', 'build_projects'])
    @patch('builtins.open', new_callable=mock_open, read_data="--- \n # valid yaml content")
    def test_build_projects_routing(self, mock_file):
        """Verify build_projects command triggers the LFXProjects pipeline."""
        Cli()
        self.mock_projects.assert_called()
        self.mock_output.return_value.load.assert_called_once()
        self.mock_output.return_value.save.assert_called_once()

    @patch('sys.argv', ['cli.py', '--silent', 'sync_members'])
    @patch('builtins.open', new_callable=mock_open, read_data="--- \n # valid yaml content")
    def test_sync_members_routing(self, mock_file):
        """Verify sync_members command triggers the LFXMembers pipeline."""
        Cli()
        # Ensure LFXMembers was initialized
        self.mock_members.assert_called()
        self.mock_landscapemembers.assert_called()
        self.mock_output.return_value.load.assert_called_once()
        self.mock_output.return_value.save.assert_called_once()

    @patch('sys.argv', ['cli.py', '--silent', 'sync_projects'])
    @patch('builtins.open', new_callable=mock_open, read_data="--- \n # valid yaml content")
    def test_sync_projects_routing(self, mock_file):
        """Verify sync_projects command triggers the LFXProjects and TACAgendaProject pipeline."""
        Cli()
        self.mock_projects.assert_called()
        self.mock_tacagendaproject.assert_called()
        self.mock_landscapemembers.assert_called()
        self.mock_output.return_value.load.assert_called_once()
        self.mock_output.return_value.save.assert_called_once()

    @patch('sys.stdout')
    @patch('sys.argv', ['cli.py', 'maketextlogo', '--name', 'OpenSource'])
    def test_maketextlogo_args(self, mock_stdout):
        """Verify logo command correctly passes arguments to SVGLogo."""
        Cli()
        self.mock_svg.assert_called_with(name='OpenSource')
        self.mock_svg.return_value.save.assert_not_called()

    @patch('sys.stdout')
    @patch('sys.argv', ['cli.py', 'maketextlogo', '--name', 'OpenSource', '--autocrop'])
    def test_maketextlogo_args_autocrop(self, mock_stdout):
        """Verify logo command correctly passes arguments to SVGLogo."""
        Cli()
        self.mock_svg.assert_called_with(name='OpenSource')
        self.mock_svg.return_value.autocrop.assert_called()

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
    @patch('builtins.open', new_callable=mock_open, read_data="--- \n # valid yaml content")
    def test_verbose_flag_sets_info_level(self, mock_file, mock_log_config):
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

    @patch('logging.Logger.debug')
    @patch('sys.argv', ['cli.py', '--log', 'debug', 'build_members'])
    @patch('lfx_landscape_tools.cli.LFXMembers', side_effect=Exception("Critical Failure"))
    @patch('argparse.ArgumentParser.print_help')
    @patch('builtins.open', new_callable=mock_open, read_data="--- \n # valid yaml content")
    def test_error_handling_prints_help(self, mock_file, mock_help, mock_lfx, mock_log_debug):
        """Ensure that if a command fails, the help message is displayed."""
        Cli()
        mock_help.assert_called_once()
        mock_log_debug.assert_called()

    @patch('sys.argv', ['cli.py', '--silent', 'build_projects'])
    @patch('builtins.open', new_callable=mock_open, read_data="--- \n # valid yaml content")
    def test_run_static(self, mock_file):
        """Verify build_projects command triggers the LFXProjects pipeline."""
        Cli.run()
        # Ensure LFXProjects was initialized
        self.mock_projects.assert_called()

    def test_extract_logos(self):
        """Verify _extract_logos recursively extracts non-null logo entries."""
        cli_manual = Cli.__new__(Cli)
        sample_yaml = {
            "landscape": [
                {
                    "name": "Category 1",
                    "subcategories": [
                        {
                            "name": "Subcategory A",
                            "items": [
                                {"name": "Item 1", "logo": "item1.svg"},
                                {"name": "Item 2", "logo": None},
                                {"name": "Item 3"},
                            ],
                        }
                    ],
                },
                {"name": "Top-level item", "logo": "toplevel.svg"},
            ]
        }

        self.assertEqual(cli_manual._extract_logos(sample_yaml), ["item1.svg", "toplevel.svg"])
        self.assertEqual(cli_manual._extract_logos({}), [])
        self.assertEqual(cli_manual._extract_logos([]), [])
        self.assertEqual(cli_manual._extract_logos(None), [])

    @patch('sys.argv', ['cli.py', '--silent', 'removestalelogos'])
    @patch('builtins.open', new_callable=mock_open, read_data="--- \n # valid yaml content")
    def test_removestalelogos_routing_and_cleanup(self, mock_file):
        """Verify removestalelogos command routes properly and deletes only unused logos."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logos_dir = Path(tmpdir) / "hosted_logos"
            logos_dir.mkdir()

            active_file = logos_dir / "active.svg"
            stale_file = logos_dir / "stale.svg"
            active_file.write_text("<svg>active</svg>", encoding="utf-8")
            stale_file.write_text("<svg>stale</svg>", encoding="utf-8")

            self.mock_config.return_value.hostedLogosDir = "hosted_logos"
            self.mock_landscapemembers.return_value.load_landscape_yaml.return_value = {
                "landscape": [{"items": [{"logo": "active.svg"}]}]
            }

            with patch('os.chdir'):
                # Verify CLI routing works with default basedir
                with patch('lfx_landscape_tools.cli.os.scandir', return_value=os.scandir(logos_dir)):
                    Cli()

            self.assertTrue(active_file.exists())
            self.assertFalse(stale_file.exists())
            self.mock_landscapemembers.assert_called_once_with(
                self.mock_config.return_value, loadData=False
            )

    @patch('lfx_landscape_tools.cli.os.remove', side_effect=FileNotFoundError)
    def test_removestalelogos_file_not_found(self, mock_remove):
        """Verify removestalelogos logs a warning if a stale file disappears before deletion."""
        cli_manual = Cli.__new__(Cli)

        with tempfile.TemporaryDirectory() as tmpdir:
            logos_dir = Path(tmpdir) / "hosted_logos"
            logos_dir.mkdir()
            (logos_dir / "ghost.svg").write_text("<svg/>", encoding="utf-8")

            self.mock_config.return_value.hostedLogosDir = "hosted_logos"
            self.mock_landscapemembers.return_value.load_landscape_yaml.return_value = {}

            args = SimpleNamespace(configfile="config.yml", basedir=tmpdir)
            with self.assertLogs(level='WARNING') as log_ctx:
                cli_manual.removestalelogos(args)

            mock_remove.assert_called_once()
            self.assertTrue(
                any("File was already deleted or does not exist." in msg for msg in log_ctx.output)
            )

    @patch('lfx_landscape_tools.cli.os.remove', side_effect=PermissionError("Access denied"))
    def test_removestalelogos_permission_error(self, mock_remove):
        """Verify removestalelogos logs an exception if deleting a stale file raises PermissionError."""
        cli_manual = Cli.__new__(Cli)

        with tempfile.TemporaryDirectory() as tmpdir:
            logos_dir = Path(tmpdir) / "hosted_logos"
            logos_dir.mkdir()
            (logos_dir / "locked.svg").write_text("<svg/>", encoding="utf-8")

            self.mock_config.return_value.hostedLogosDir = "hosted_logos"
            self.mock_landscapemembers.return_value.load_landscape_yaml.return_value = {}

            args = SimpleNamespace(configfile="config.yml", basedir=tmpdir)
            with self.assertLogs(level='ERROR') as log_ctx:
                cli_manual.removestalelogos(args)

            mock_remove.assert_called_once()
            self.assertTrue(
                any(
                    "Permission denied: file may be open or read-only." in msg
                    for msg in log_ctx.output
                )
            )

    @patch('builtins.print')
    def test_isvalidlogo_valid(self, mock_print):
        """Verify isvalidlogo prints valid message when SVGLogo.isValid() returns True."""
        cli_manual = Cli.__new__(Cli)
        mock_logo = self.mock_svg(filename="valid.svg")
        mock_logo.isValid.return_value = True

        args = argparse.Namespace(filename=mock_logo)
        cli_manual.isvalidlogo(args)

        self.mock_svg.return_value.isValid.assert_called_once()
        mock_print.assert_called_once_with("Logo is valid")

    @patch('builtins.print')
    def test_isvalidlogo_invalid(self, mock_print):
        """Verify isvalidlogo prints invalid message when SVGLogo.isValid() returns False."""
        cli_manual = Cli.__new__(Cli)
        mock_logo = self.mock_svg(filename="invalid.svg")
        mock_logo.isValid.return_value = False

        args = argparse.Namespace(filename=mock_logo)
        cli_manual.isvalidlogo(args)

        self.mock_svg.return_value.isValid.assert_called_once()
        mock_print.assert_called_once_with("Logo is not valid")

    @patch('builtins.print')
    @patch('sys.argv', ['cli.py', '--silent', 'isvalidlogo', '-f', 'test.svg'])
    def test_isvalidlogo_routing(self, mock_print):
        """Verify isvalidlogo subcommand routes arguments to SVGLogo."""
        self.mock_svg.return_value.isValid.return_value = True
        Cli()
        self.mock_svg.assert_called_once_with(filename='test.svg')
        mock_print.assert_called_once_with("Logo is valid")

if __name__ == "__main__":
    unittest.main()
