# LFX Landscape Tools

[![License](https://img.shields.io/github/license/jmertic/landscape-tools)](LICENSE)
[![CI](https://github.com/jmertic/landscape-tools/workflows/CI/badge.svg)](https://github.com/jmertic/landscape-tools/actions?query=workflow%3ACI)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=jmertic_lfx-landscape-tools&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=jmertic_lfx-landscape-tools)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=jmertic_lfx-landscape-tools&metric=coverage)](https://sonarcloud.io/summary/new_code?id=jmertic_lfx-landscape-tools)

This project contains tools that make building and maintaining a [landscape](https://github.com/cncf/landscapeapp) easier by pulling data from LFX on projects and members. 

It is an evolution of the former [landscape-tools](https://github.com/jmertic/landscape-tools), with a refactor to add the ability to pull projects from LFX and generate text logos when a pure SVG does not exist. Additional differences include:

- Only leverage LFX data for members and projects; no longer looks up in CrunchBase or other landscapes.
- Pull review data from a TAC repo using a specific project format, if used.
- More verbose error messages that improve debugging.

## Installation and Configuration instructions

See [INSTRUCTIONS.md](./INSTRUCTIONS.md).

## Contributing

Feel free to send [issues](/issues) or [pull requests](/pulls) ( with a DCO signoff of course :-) ) in accordance with the [contribution guidelines](CONTRIBUTING.md)
