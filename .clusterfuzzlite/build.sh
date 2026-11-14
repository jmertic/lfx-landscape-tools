#!/bin/bash -eu
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# Builds the Atheris fuzz harnesses in fuzz/ for ClusterFuzzLite.

pip3 install --no-cache-dir --require-hashes -r .clusterfuzzlite/requirements.txt

# Bundle X11/Cairo shared libraries omitted by PyInstaller's default exclusion list
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

  compile_python_fuzzer "$fuzzer" \
    --paths=. \
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
