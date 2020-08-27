#!/bin/sh -e

export PREFIX=""
if [ -d 'venv' ] ; then
    export PREFIX="venv/bin/"
fi
export SOURCE_FILES="tokamak tests"

set -x

${PREFIX}pytest
${PREFIX}black $SOURCE_FILES
${PREFIX}mypy $SOURCE_FILES
${PREFIX}isort $SOURCE_FILES

