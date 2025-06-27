#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

from lfx_landscape_tools.config import Config
from lfx_landscape_tools.lfxmembers import LFXMembers
from lfx_landscape_tools.lfxprojects import LFXProjects
from lfx_landscape_tools.landscapemembers import LandscapeMembers
from lfx_landscape_tools.landscapeoutput import LandscapeOutput
from lfx_landscape_tools.svglogo import SVGLogo
from lfx_landscape_tools.tacagendaproject import TACAgendaProject

from datetime import datetime
from argparse import ArgumentParser,FileType
import os
import subprocess
from os import path
import logging
import sys

class Cli:

    _starttime = None
    _defaultconfigfile = 'config.yml'

    def __init__(self):
        self._starttime = datetime.now()

        parser = ArgumentParser("Collection of tools for working with a landscape")
        parser.add_argument("-s", "--silent", dest="silent", action="store_true", help="Suppress all messages")
        parser.add_argument("-l", "--log", dest="loglevel", default="error", choices=['debug', 'info', 'warning', 'error', 'critical'], help="logging level")
        parser.add_argument("-v", "--verbose", dest="verbose", action='store_true', help="Verbose output (i.e. show all INFO level messages in addition to WARN and above - equivalent to `--log info`)")
        subparsers = parser.add_subparsers(help='sub-command help')
        
        buildlandscapemembers_parser = subparsers.add_parser("build_members", help="Replace current items with latest from LFX")
        buildlandscapemembers_parser.add_argument("-c", "--config", dest="configfile", default=self._defaultconfigfile, type=FileType('r'), help="name of YAML config file")
        buildlandscapemembers_parser.add_argument("-d", "--dir", dest="basedir", default=".", type=self._dir_path, help="path to where landscape directory is")
        buildlandscapemembers_parser.set_defaults(func=self.buildmembers)
        
        buildlandscapeprojects_parser = subparsers.add_parser("build_projects", help="Replace current items with latest from LFX")
        buildlandscapeprojects_parser.add_argument("-c", "--config", dest="configfile", default=self._defaultconfigfile, type=FileType('r'), help="name of YAML config file")
        buildlandscapeprojects_parser.add_argument("-d", "--dir", dest="basedir", default=".", type=self._dir_path, help="path to where landscape directory is")
        buildlandscapeprojects_parser.set_defaults(func=self.buildprojects)
        
        synclandscapeprojects_parser = subparsers.add_parser("sync_projects", help="Sync current items with latest from LFX")
        synclandscapeprojects_parser.add_argument("-c", "--config", dest="configfile", default=self._defaultconfigfile, type=FileType('r'), help="name of YAML config file")
        synclandscapeprojects_parser.add_argument("-d", "--dir", dest="basedir", default=".", type=self._dir_path, help="path to where landscape directory is")
        synclandscapeprojects_parser.set_defaults(func=self.syncprojects)
        
        maketextlogo_parser = subparsers.add_parser("maketextlogo", help="Create a text pure SVG logo")
        maketextlogo_parser.add_argument("-n", "--name", dest="name", required=True, help="Name to appear in logo")
        maketextlogo_parser.add_argument("--autocrop", dest="autocrop", action='store_true', help="Process logo with autocrop")
        maketextlogo_parser.add_argument("-o", "--output", dest="filename", help="Filename to save created logo to")
        maketextlogo_parser.set_defaults(func=self.maketextlogo)

        validate_parser = subparsers.add_parser("validatedata", help="Validate landscape data file")
        validate_parser.add_argument("filename", help="Landscape data file name", default="landscape.yml")
        validate_parser.set_defaults(func=self.validatedata)

        args = parser.parse_args()

        levels = {
            'critical': logging.CRITICAL,   # errors that mean an immediate stop
            'error': logging.ERROR,         # general errors that will effect the output
            'warn': logging.WARNING,        # errors that can be caught and corrected
            'warning': logging.WARNING,
            'info': logging.INFO,           # infomational messages
            'debug': logging.DEBUG          # messages to help debug things misbehaving ;-)
        }
        if args.verbose:
            args.loglevel = 'info'
        handlers = [logging.FileHandler("debug.log",mode="w")]
        if not args.silent:
            handlers.append(logging.StreamHandler(sys.stdout))
        logging.basicConfig(
            level=levels.get(args.loglevel.lower()),
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=handlers
        )

        try:
            args.func(args)
        except AttributeError as e:
            logging.getLogger().debug(e)
            parser.print_help()
        
        logging.getLogger().info("This took {} seconds".format(datetime.now() - self._starttime))

    @staticmethod
    def run():
        Cli() 

    def _dir_path(self,path):
        if os.path.isdir(path):
            return path
        else:
            raise argparse.ArgumentTypeError(f"readable_dir:{path} is not a valid path")
    
    def buildmembers(self,args):
        config = Config(args.configfile,view='members')
        landscapeoutput = LandscapeOutput(config=config)
        landscapeoutput.load(members=LFXMembers(config=config))
        landscapeoutput.save()
        
        logging.getLogger().info("Successfully processed {} members and skipped {} members".format(landscapeoutput.itemsProcessed,landscapeoutput.itemsErrors))

    def buildprojects(self,args):
        config = Config(args.configfile,view='projects')
        landscapeoutput = LandscapeOutput(config=config)
        landscapeoutput.load(members=LFXProjects(config=config))
        landscapeoutput.save()
        
        logging.getLogger().info("Successfully processed {} projects and skipped {} projects".format(landscapeoutput.itemsProcessed,landscapeoutput.itemsErrors))

    def syncprojects(self,args):
        config = Config(args.configfile,view='projects')
        items = LFXProjects(config=config)
        logging.getLogger().info("Overlaying current Landscape data")
        items.overlay(memberstooverlay=LandscapeMembers(config=config))
        logging.getLogger().info("Overlaying TAC Agenda Project data")
        items.overlay(memberstooverlay=TACAgendaProject(config=config))
        # yes, this is intentional :). This ensures the LFX data is the predominate source of truth
        logging.getLogger().info("Overlaying LFX Projects data")
        items.overlay(memberstooverlay=LFXProjects(config=config))
        # also intentional, to overlay extra field dates where the TAC Agenda is the source of truth
        logging.getLogger().info("Overlaying TAC Agenda Project data 'extra' field")
        items.overlay(memberstooverlay=TACAgendaProject(config=config),onlykeys=['extra'])
        landscapeoutput = LandscapeOutput(config=config)
        landscapeoutput.load(members=items)
        landscapeoutput.save()
        
        logging.getLogger().info("Successfully processed {} projects and skipped {} projects".format(landscapeoutput.itemsProcessed,landscapeoutput.itemsErrors))

    def maketextlogo(self,args):
        svglogo = SVGLogo(name=args.name)

        if args.autocrop:
            svglogo.autocrop()

        if args.filename:
            svglogo.save(args.filename)
        else:
            print(svglogo)

        return True

    def validatedata(self,args):
        schema = "https://raw.githubusercontent.com/cncf/landscape2/refs/heads/main/docs/config/schema/data.schema.json"
        filename = args.filename
        subprocess.run("check-jsonschema --schemafile {schema} {filename}".format(schema=schema,filename=filename), shell=True)
