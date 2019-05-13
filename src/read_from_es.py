#!/usr/bin/env python3
"""
Read log records from Elasticsearch. Emits a stream to `stdout`.
"""

import os
from argparse import ArgumentParser

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
import settings


def run(constants):
    host = constants['host'] or os.getenv('ES_HOST')
    index = constants['index'] or os.getenv('ES_INDEX')
    user = constants['username'] or os.getenv('ES_USER')
    password = constants['password'] or os.getenv('ES_PASSWORD')

    client = Elasticsearch([host], http_auth=(user, password))
    s = Search(using=client, index=index)

    if constants['is_stream']:
        for hit in s:
            for result in hit.results:
                for line in result.body.splitlines():
                    if len(line) > 0:
                        print(line)


if __name__ == '__main__':
    # read args
    parser = ArgumentParser(description='Run Elasticsearch Reader')
    parser.add_argument('--host', dest='host', type=str, help='elasticsearch host')
    parser.add_argument('--index', dest='index', type=str, help='elasticsearch index')
    parser.add_argument('--user', dest='username', type=str, help='elasticsearch user')
    parser.add_argument('--password', dest='password', type=str, help='elasticsearch password')
    parser.add_argument('--stream', dest='is_stream', help='set streaming mode', action='store_true')
    parser.set_defaults(is_stream=False)
    args = parser.parse_args()

    run(vars(args))
