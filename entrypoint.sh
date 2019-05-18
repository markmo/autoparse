#!/usr/bin/env bash

export PYTHONPATH=.  # add current directory to package path
gunicorn -b 0.0.0.0:8000 api.endpoints:app
