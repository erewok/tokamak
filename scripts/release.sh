#!/bin/sh -e

export PREFIX=""
if [ -d 'venv' ] ; then
    export PREFIX="venv/bin/"
fi
if [ -d '.venv' ] ; then
    export PREFIX=".venv/bin/"
fi
export SOURCE_FILES="tokamak tests"

set -x

poetry build
${PREFIX}twine check dist/*
${PREFIX}twine upload dist/*