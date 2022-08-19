#!/bin/sh -e

poetry build
python -m twine check dist/*
python -m twine upload dist/*