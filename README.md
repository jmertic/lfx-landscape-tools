# LFX Landscape Tools

[![License](https://img.shields.io/github/license/jmertic/lfx-landscape-tools)](LICENSE)
[![CI](https://github.com/jmertic/lfx-landscape-tools/workflows/CI/badge.svg)](https://github.com/jmertic/lfx-landscape-tools/actions?query=workflow%3ACI)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=jmertic_lfx-landscape-tools&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=jmertic_lfx-landscape-tools)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=jmertic_lfx-landscape-tools&metric=coverage)](https://sonarcloud.io/summary/new_code?id=jmertic_lfx-landscape-tools)

This project contains tools that make building and maintaining a [landscape](https://github.com/cncf/landscapeapp) easier by pulling data from LFX on projects and members. 

It is an evolution of the former [landscape-tools](https://github.com/jmertic/landscape-tools), with a refactor to add the ability to pull projects from LFX and generate text logos when a pure SVG does not exist. Additional differences include:

- Only leverage LFX data for members and projects; no longer looks up in CrunchBase or other landscapes.
- Pull review data from a TAC repo using a specific project format, if used.
- More verbose error messages that improve debugging.

## Setting up the GitHub Action

1) Add [secrets](https://docs.github.com/en/actions/reference/encrypted-secrets) for `PAT`, which is a [GitHub Personal Authorization Token](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token) set for the `repo` scope.
2) [Add a new label](https://docs.github.com/en/github/managing-your-work-on-github/managing-labels#creating-a-label) - `automated-build`. This is for this workflow to work and shouldn't be used for anything else.
3) Add the following code to a `build.yml` file in your landscape repo's `.github/workflows/` directory.

```yaml
name: Build Landscape from LFX

on:
  workflow_dispatch:
  schedule:
  - cron: "0 4 * * *"

jobs:
  build:
    runs-on: ubuntu-24.04
    steps:
      - name: Harden Runner
        uses: step-security/harden-runner@91182cccc01eb5e619899d80e4e971d6181294a7 # v2.10.1
        with:
          egress-policy: audit
      - uses: jmertic/lfx-landscape-tools@main
        with:
          project_processing: skip # see options in action.yml
        env:
          token: ${{ secrets.PAT }}
          repository: ${{ github.repository }}
          ref: ${{ github.ref }}
```
4) Add the following code to a `validate.yml` file in your landscape repo's `.github/workflows/` directory.

```yaml
name: Validate Landscape

on:
  merge_group:
  pull_request:
    branches:
      - main
      - master

jobs:
  validate-landscape:
    runs-on: ubuntu-latest
    name: "Validate landscape.yml file"
    steps:
      - name: Harden Runner
        uses: step-security/harden-runner@91182cccc01eb5e619899d80e4e971d6181294a7 # v2.10.1
        with:
          egress-policy: audit

      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - uses: cncf/landscape2-validate-action@7f299c46e9b03b4e8bc2896882734fb0b0756b37 # v2.0.0
        with:
          target_kind: data
          target_path: ./landscape.yml
      - uses: pascalgn/automerge-action@7961b8b5eec56cc088c140b56d864285eabd3f67 # v0.16.4
        if: success()
        env:
          GITHUB_TOKEN: "${{ secrets.PAT }}"
          MERGE_LABELS: "automated-build"
          MERGE_RETRY_SLEEP: 300000
          MERGE_METHOD: "squash"
```

## Local install

You can install this tool on your local computer via `pipx`

```bash
pipx install git+https://github.com/jmertic/lfx-landscape-tools.git
```

Similarly, you can use the command below to upgrade your local install.

```bash
pipx upgrade lfx-landscape-tools
```

You can then use the `lfxlandscape` command to run the various commands. Use `lfxlandscape --help` for the options.

## Contributing

Feel free to send [issues](/issues) or [pull requests](/pulls) ( with a DCO signoff of course :-) ) in accordance with the [contribution guidelines](CONTRIBUTING.md)
