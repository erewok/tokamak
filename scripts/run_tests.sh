#!/bin/sh -e

export PREFIX=""
if [ -d 'venv' ] ; then
    export PREFIX="venv/bin"
fi
if [ -d '.venv' ] ; then
    export PREFIX=".venv/bin"
fi
export SOURCE_FILES="tokamak tests"

"${PREFIX}/black" --check --diff $SOURCE_FILES
"${PREFIX}/isort" --check --diff --project=tokamak $SOURCE_FILES
# "${PREFIX}/mypy" $SOURCE_FILES
"${PREFIX}/pytest"
