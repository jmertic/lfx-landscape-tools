# LFX Landscape Tools

[![License](https://img.shields.io/github/license/jmertic/lfx-landscape-tools)](LICENSE)
[![CI](https://github.com/jmertic/lfx-landscape-tools/workflows/CI/badge.svg)](https://github.com/jmertic/lfx-landscape-tools/actions?query=workflow%3ACI+branch%3Amain)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=jmertic_lfx-landscape-tools&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=jmertic_lfx-landscape-tools)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=jmertic_lfx-landscape-tools&metric=coverage)](https://sonarcloud.io/summary/new_code?id=jmertic_lfx-landscape-tools)

This project contains tools that make building and maintaining a [landscape](https://github.com/cncf/landscapeapp) easier by pulling data from LFX on projects and members. 

It is an evolution of the former [landscape-tools](https://github.com/jmertic/landscape-tools), with a refactor to add the ability to pull projects from LFX and generate text logos when a pure SVG does not exist. Additional differences include:

- Only leverage LFX data for members and projects; no longer look up in CrunchBase or other landscapes.
- Pull review data from a TAC repo using a specific project format, if used.
- More verbose error messages that improve debugging.

## Configuration

The default configuration for the build is located in the `config.yml` file, which you should put in the top directory in your landscape repo ( i.e. the same place you would have the `landscape.yml` file ). All options are defined at [lfx_landscape_tools/config.py](lfx_landscape_tools/config.py). See the example below for a simple `config.yml` file for building a members-only landscape.

```yaml
# Membership levels; name is the membership level name in LFX; category is the matching subcategory name in the landscape
landscapeMemberClasses: 
   - name: Steering Membership
     category: Steering
   - name: General Membership
     category: General
# Slug for the project from LFX
slug: alliance-for-open-usd-fund-aousdf
# Category name for members
landscapeMemberCategory: AOUSD Members
```

## Setting up the GitHub Action

1) Review the permissions for the `GITHUB_TOKEN` for your repository ( more details [here](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication#permissions-for-the-github_token) ). Note that you need to ensure `GITHUB_TOKEN` has the permission to merge PRs (more [here](https://docs.github.com/en/organizations/managing-organization-settings/disabling-or-limiting-github-actions-for-your-organization#preventing-github-actions-from-creating-or-approving-pull-requests)).
   - If you cannot set `GITHUB_TOKEN` permissions as stated, the fallback option is to add a [repository secret](https://docs.github.com/en/actions/reference/encrypted-secrets) for `PAT`, which is a [GitHub Personal Authorization Token](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token) set for the `read:org`, `read:project`, and `repo` scope.
3) [Add a new label](https://docs.github.com/en/github/managing-your-work-on-github/managing-labels#creating-a-label) - `automated-build`. This is for this workflow to work and shouldn't be used for anything else.
4) Add the following code to a `build.yml` file in your landscape repo's `.github/workflows/` directory.
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
      - uses: jmertic/lfx-landscape-tools@20a188cdc3f2ee0318047b50de7e9b75b8f48268 # 20250528
        with:
          project_processing: skip # see options in action.yml
        env:
          token: ${{ secrets.GITHUB_TOKEN }}
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
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - uses: cncf/landscape2-validate-action@7f299c46e9b03b4e8bc2896882734fb0b0756b37 # v2.0.0
        with:
          target_kind: data
          target_path: ./landscape.yml
```

5) Run the `Build Landscape from LFX` GitHub Action following the instructions for [manually running a GitHub Action](https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-workflow-runs/manually-running-a-workflow) to test that it all works.

### Auto-merging landscape build changes
 
If the build results in data that differs from the current data in the landscape, a pull request is created to apply those changes. This pull request is by default set to be [automatically merged](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/automatically-merging-a-pull-request) only if the following conditions are met.

- The target repository must have **[Allow auto-merge](https://docs.github.com/en/github/administering-a-repository/managing-auto-merge-for-pull-requests-in-your-repository)** enabled in settings.
- The pull request base must have a branch protection rule with at least one requirement enabled.
- The pull request must be in a state where requirements have not yet been satisfied. If the pull request is in a state where it can already be merged, the action will merge it immediately without enabling auto-merge.

## Local install

You can install this tool on your local computer via [`pipx`](https://pipx.pypa.io).

```bash
pipx install git+https://github.com/jmertic/lfx-landscape-tools.git
```

Similarly, you can use the command below to upgrade your local install.

```bash
pipx upgrade lfx-landscape-tools
```

You can then use the `lfx_landscape` command to run the various commands. Use `lfx_landscape --help` for the options.

## Contributing

Feel free to send [issues](/issues) or [pull requests](/pulls) ( with a DCO signoff of course :-) ) in accordance with the [contribution guidelines](CONTRIBUTING.md)
