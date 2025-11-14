#!/usr/bin/env bash

set -e
set -x

coverage run --source=swx_api -m pytest
coverage report --show-missing
coverage html --title "${@-coverage}"
