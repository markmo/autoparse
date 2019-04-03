#!/usr/bin/env bash

source activate autoparse  # activate conda environment for dependencies
export PYTHONPATH=.        # add current directory to package path
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" > /dev/null 2>&1 && pwd )"  # get directory of this script
python ${DIR}/filter.py
