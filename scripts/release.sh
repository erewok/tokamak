#!/bin/sh -e

poetry build
twine check dist/*
twine upload dist/*