FROM gcr.io/oss-fuzz-base/base-builder-python
# pycairo builds from source on Linux and needs the cairo headers.
RUN apt-get update && apt-get install -y --no-install-recommends libcairo2-dev pkg-config zip
RUN pip3 install --upgrade pip poetry pyinstaller jaraco.text
COPY . $SRC/lfx-landscape-tools
WORKDIR $SRC/lfx-landscape-tools
COPY .clusterfuzzlite/build.sh $SRC/
