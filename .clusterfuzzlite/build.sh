#!/bin/bash -eu
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# Builds the Atheris fuzz harnesses in fuzz/ for ClusterFuzzLite.

# The project declares Python >= 3.12, but the OSS-Fuzz base image ships an
# older Python. The code and its dependencies run fine on it, so skip the check.
pip3 install --no-cache-dir --require-hashes -r .clusterfuzzlite/requirements.txt
pip3 install --no-cache-dir --no-deps --ignore-requires-python .

# PyInstaller excludes X11/Cairo system libraries (libxcb, libX11, fontconfig, etc.)
# by default, which are absent in the headless ClusterFuzzLite runner image.
# Find _cairo*.so on disk without importing it (it is compiled with sanitizer flags
# that require LD_PRELOAD of sanitizer_with_fuzzer.so at runtime).
CAIRO_SO=$(find /usr/local/lib -path '*/cairo/_cairo*.so' -print -quit)
EXTRA_BINS=()
while IFS= read -r lib; do
  case "$(basename "$lib")" in
    libc.so*|libm.so*|libpthread.so*|libdl.so*|librt.so*|ld-linux*|libgcc_s.so*|libstdc++.so*|libasan*|libubsan*) ;;
    *) EXTRA_BINS+=(--add-binary "$lib:.") ;;
  esac
done < <(ldd "$CAIRO_SO" | awk '/=> \// {print $3}')

for fuzzer in fuzz/fuzz_*.py; do
  name=$(basename -s .py "$fuzzer")

  # python-slugify imports text_unidecode dynamically, so PyInstaller misses it.
  compile_python_fuzzer "$fuzzer" \
    --paths=fuzz \
    --collect-all text_unidecode \
    --collect-all jaraco \
    "${EXTRA_BINS[@]}"

  if [ -d "fuzz/corpus/$name" ]; then
    zip -qj "$OUT/${name}_seed_corpus.zip" "fuzz/corpus/$name"/*
  fi
done

cp fuzz/svg.dict "$OUT/fuzz_svglogo_validate.dict"
cp fuzz/landscape.dict "$OUT/fuzz_landscape_yaml.dict"
