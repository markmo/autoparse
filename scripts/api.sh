#!/usr/bin/env bash

source activate autoparse > /dev/null 2>&1  # activate conda environment for dependencies
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" > /dev/null 2>&1 && pwd )"  # get directory of this script
export PYTHONPATH=${DIR}/../src             # add current directory to package path
gunicorn api.endpoints:app
