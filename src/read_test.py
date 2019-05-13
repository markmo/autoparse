#!/usr/bin/env python3
"""
Simulates `read_from_es.py` by reading from a file instead.
"""

from argparse import ArgumentParser


def run(constants):
    with open(constants['filename'], 'r') as f:
        for line in f:
            print(line.strip())


if __name__ == '__main__':
    # read args
    parser = ArgumentParser(description='Run Reader Test')
    parser.add_argument('--filename', dest='filename', type=str, help='input filename')
    args = parser.parse_args()

    run(vars(args))
