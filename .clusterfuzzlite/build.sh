#!/bin/bash -eu
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# Builds the Atheris fuzz harnesses in fuzz/ for ClusterFuzzLite.

# The project declares Python >= 3.12, but the OSS-Fuzz base image ships an
# older Python. The code and its dependencies run fine on it, so skip the check.
pip3 install --ignore-requires-python .

for fuzzer in fuzz/fuzz_*.py; do
  name=$(basename -s .py "$fuzzer")

  # python-slugify imports text_unidecode dynamically, so PyInstaller misses it.
  compile_python_fuzzer "$fuzzer" --paths=fuzz --collect-all text_unidecode --collect-all jaraco

  if [ -d "fuzz/corpus/$name" ]; then
    zip -qj "$OUT/${name}_seed_corpus.zip" "fuzz/corpus/$name"/*
  fi
done

cp fuzz/svg.dict "$OUT/fuzz_svglogo_validate.dict"
cp fuzz/landscape.dict "$OUT/fuzz_landscape_yaml.dict"
