FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:21f6fab17ace4dc76e1c56de91ee95d3d03da021df94b41056ba036f6c6f55e9

# pycairo builds from source on Linux and needs the cairo headers.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2-dev \
    pkg-config \
    zip \
  && rm -rf /var/lib/apt/lists/*

COPY .clusterfuzzlite/requirements-build.txt /tmp/requirements-build.txt
RUN pip3 install --no-cache-dir --require-hashes -r /tmp/requirements-build.txt

COPY . $SRC/lfx-landscape-tools
WORKDIR $SRC/lfx-landscape-tools
COPY .clusterfuzzlite/build.sh $SRC/
