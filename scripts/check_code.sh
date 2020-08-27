#!/bin/sh -e

export PREFIX=""
if [ -d 'venv' ] ; then
    export PREFIX="venv/bin/"
fi
export SOURCE_FILES="tokamak tests"

set -x

${PREFIX}isort --check --diff --project=tokamak $SOURCE_FILES
${PREFIX}black --check --diff $SOURCE_FILES
${PREFIX}flake8 $SOURCE_FILES
${PREFIX}mypy $SOURCE_FILES

