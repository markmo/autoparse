#!/usr/bin/env python3
"""
Extract entities using rules and NLP, and templates using Spell, from log lines.
"""

import hashlib
import json
import re
import sys
from argparse import ArgumentParser
from datetime import datetime
from typing import Tuple

import spacy

from config import REGEXS
from load import load
from pyspell.spell import LogParser
from pyspell.spell_stream import get_span, ioc_parse, LCSMap, make_log_format_regex, preprocess
from streaming_app import app, log_keys_topic, parsed_logs_topic, raw_logs_topic


class LogStreamParser(object):

    def __init__(self, log_format: str = None, use_nlp: bool = False):
        self.use_nlp = use_nlp
        self.nlp = spacy.load('en_core_web_sm') if use_nlp else None
        self.slm = LCSMap(r'\s+')
        if log_format is None:
            log_format = '<content>'

        _, self.regex = make_log_format_regex(log_format)
        self.log_keys = []

    def set_log_format(self, log_format: str) -> None:
        _, self.regex = make_log_format_regex(log_format)

    def parse(self, jsonstr: str) -> Tuple[str, object]:
        # noinspection PyBroadException
        try:
            log = json.loads(jsonstr.strip())
            line = re.sub(r'[^\x00-\x7F]+', '<NASCII>', log['line'].strip())
            match = self.regex.search(line)
            metadata = log['metadata']
            # for group in match.groups():
            #     if group != 'content':
            #         metadata[group] = match.group(group)

            content = match.group('content')
            seq = re.split(r'\s+', content)  # compute before preprocess

            # handle defanged indicators of compromise
            # content, params1 = ioc_parse(content)

            # catch the rest
            content, params2 = preprocess(content, REGEXS)
            # params = params1 + params2
            params = params2
            ps = []
            # TODO include the refanged value if present
            for p in params:
                ps.append({
                    'char_start': p[0],
                    'char_end': p[1],
                    'token_start': p[4],
                    'token_end': p[5],
                    'entity': p[3],
                    'value': p[2]
                })

            # extract entities using NLP
            # I'm not expecting anything from the out-of-the-box model
            # it must be trained using domain-specific data.
            if self.use_nlp:
                doc = self.nlp(content)
                for ent in doc.ents:
                    ps.append({
                        'char_start': ent.start_char,
                        'char_end': ent.end_char,
                        'token_start': ent.start,
                        'token_end': ent.end,
                        'entity': ent.label,
                        'value': ent.text
                    })

            obj = self.slm.insert(content)
            for param in obj.param(content):
                for slot in param:
                    token_start, param, prev_token, next_token = slot
                    char_start, char_end = get_span(seq, token_start)
                    entity = {
                        'char_start': char_start,
                        'char_end': char_end,
                        'token_start': token_start,
                        'token_end': token_start + 1,
                        'entity': 'unnamed',
                        'value': param
                    }
                    if prev_token is not None:
                        entity['prev_token'] = prev_token

                    if next_token is not None:
                        entity['next_token'] = next_token

                    ps.append(entity)

            ps.sort(key=lambda x: x['char_start'])
            log_id = hashlib.md5((content + str(datetime.now())).encode('utf-8')).hexdigest()[0:8]
            log_key = obj.lcsseq()
            new_log_key = None
            if log_key not in self.log_keys:
                self.log_keys.append(log_key)
                new_log_key = log_key

            return new_log_key, json.dumps({
                'log_id': log_id,
                'line': line,
                'message': ' '.join(seq),
                'log_key': log_key,
                'event_id': obj.getobjid(),
                'params': ps,
                'id': log['id'],
                'source_collection': log['source_collection'],
                'metadata': metadata
            })

        except Exception as e:
            raise e

    def process_stdin(self):
        for jsonstr in sys.stdin.readlines():
            log_key, output = self.parse(jsonstr)
            print(output)
            if log_key is not None:
                # TODO hack to enable forked outputs
                # a more robust streaming infrastructure such as `Faust <https://github.com/robinhood/faust>`_
                # with a Kafka broker would be the way to go
                print(log_key, file=sys.stderr)


parser = LogStreamParser()


@app.agent(log_keys_topic)
async def write_log_keys(log_keys):
    with open('/tmp/log_keys.txt', 'w') as f:
        async for log_key in log_keys:
            f.write(log_key + '\n')


@app.agent(parsed_logs_topic)
async def write_parsed_logs(parsed_logs):
    with open('/tmp/parsed_logs.jsonl', 'w') as f:
        async for log in parsed_logs:
            f.write(log + '\n')


@app.agent(raw_logs_topic)
async def parse(raw_logs):
    async for jsonstr in raw_logs:
        log_key, log = parser.parse(jsonstr)
        if log_key is not None:
            await write_log_keys.send(value=log_key)

        await write_parsed_logs.send(value=log)
        await load.send(value=log)


def run(constants):
    log_format = constants['log_format'] or '<content>'
    if constants['is_stream']:
        parser.set_log_format(log_format)
        parser.process_stdin()
    else:
        tau = constants['tau'] or 0.5
        output_dir = constants['output_dir'] or 'Spell_result/'
        log_parser = LogParser(constants['log_dir'], constants['filename'], output_dir, log_format, tau, REGEXS)
        log_parser.parse(constants['filename'])


if __name__ == '__main__':
    # read args
    arg_parser = ArgumentParser(description='Run Spell parser')
    arg_parser.add_argument('--in-dir', dest='log_dir', type=str, help='log directory')
    arg_parser.add_argument('--filename', dest='filename', type=str, help='log file')
    arg_parser.add_argument('--out-dir', dest='output_dir', type=str, help='output directory')
    arg_parser.add_argument('--log-format', dest='log_format', type=str, help='log format')
    arg_parser.add_argument('--tau', dest='tau', type=float, help='tau')
    arg_parser.add_argument('--stream', dest='is_stream', help='set streaming mode', action='store_true')
    arg_parser.set_defaults(is_stream=False)
    args = arg_parser.parse_args()

    run(vars(args))
