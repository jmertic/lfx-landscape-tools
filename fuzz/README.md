# Fuzzing

Fuzz harnesses for lfx-landscape-tools, written with [Atheris](https://github.com/google/atheris)
and run in CI by [ClusterFuzzLite](https://google.github.io/clusterfuzzlite/).

| Harness | What it fuzzes |
|---|---|
| `fuzz_svglogo_validate.py` | `SVGLogo.is_valid()` – XML parsing and checks on logo SVGs |
| `fuzz_svglogo_generate.py` | `SVGLogo(name=...)` – rendering a placeholder logo from a name with cairo |
| `fuzz_member.py` | `Member` setters (`homepage_url`, `repo_url`, `crunchbase`, `linkedin`, `twitter`, `logo`, `extra`), `to_landscape_item_attributes()` and `overlay()` |
| `fuzz_landscape_yaml.py` | `LandscapeMembers` loading and walking a `landscape.yml` file |

`offline.py` stubs out every network call and arbitrary file read, so the
harnesses run without network access.

## Running locally

```sh
poetry install
poetry run pip install atheris
mkdir -p /tmp/corpus
poetry run python fuzz/fuzz_member.py /tmp/corpus -max_total_time=300
```

The SVG validator and landscape harnesses work much better with their seed
corpus and dictionary:

```sh
poetry run python fuzz/fuzz_svglogo_validate.py /tmp/corpus fuzz/corpus/fuzz_svglogo_validate -dict=fuzz/svg.dict
poetry run python fuzz/fuzz_landscape_yaml.py /tmp/corpus fuzz/corpus/fuzz_landscape_yaml -dict=fuzz/landscape.dict
```

To reproduce a crash, pass the crashing input file instead of a corpus directory:

```sh
poetry run python fuzz/fuzz_member.py crash-<hash>
```

## In CI

- `.github/workflows/cflite_pr.yml` fuzzes every pull request for 10 minutes.
- `.github/workflows/cflite_batch.yml` fuzzes `main` for an hour each day.

The build is defined in `.clusterfuzzlite/`. Any harness named `fuzz/fuzz_*.py`
is picked up automatically; a seed corpus in `fuzz/corpus/<harness name>/` is
packaged with it.
