#!/bin/sh -e

set -Eeuxo
export SOURCE_FILES="tokamak tests"

poetry run black --check --diff $SOURCE_FILES
poetry run isort --check --diff --project=tokamak $SOURCE_FILES
# poetry run mypy $SOURCE_FILES
poetry run pytest
