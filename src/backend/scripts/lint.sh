#!/usr/bin/env bash

set -e
set -x

mypy swx_api
ruff check swx_api
ruff format swx_api --check
