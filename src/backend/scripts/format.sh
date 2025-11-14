#!/bin/sh -e
set -x

ruff check swx_api scripts --fix
ruff format swx_api scripts
