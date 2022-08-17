#!/bin/sh -e

poetry build
poetry run twine check dist/*
poetry run twine upload dist/*