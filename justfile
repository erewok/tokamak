# just manual: https://github.com/casey/just#readme

_default:
    just --list

# Install dependencies used by this project
bootstrap default="3.12":
    uv venv --python {{default}}
    just sync

# Sync dependencies with environment
sync:
    uv sync

# Build the project as a package (uv build)
build *args:
    uv build

# Run the code formatter
format:
    uv run ruff format tokamak tests

# Run code quality checks
check:
    #!/bin/bash -eux
    uv run ruff check tokamak tests

# Run mypy checks
check-types:
    #!/bin/bash -eux
    uv run mypy tokamak

# Run all tests locally
test *args:
    #!/bin/bash -eux
    uv run pytest {{args}}

# Run the project tests for CI environment (e.g. with code coverage)
ci-test coverage_dir='./coverage':
    uv run pytest --cov=tokamak --cov-report xml --junitxml=./coverage/unittest.junit.xml

# Run the API server
examples name:
    uv run --examples {{name}}