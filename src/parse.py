#!/usr/bin/env python3
"""
Extract entities using rules and NLP, and templates using Spell, from log lines.
"""

import hashlib
import json
import os
import re
import sys
from argparse import ArgumentParser
from datetime import datetime

import spacy

from config import REGEXS
from pyspell.spell import LogParser
from pyspell.spell_stream import get_span, ioc_parse, LCSMap, make_log_format_regex, preprocess


# noinspection SpellCheckingInspection
def run(constants):
    # root_dir = os.path.dirname(__file__)
    nlp = spacy.load('en_core_web_sm')
    log_format = constants['log_format'] or '<process>: <content>'
    if constants['is_stream']:
        slm = LCSMap(r'\s+')
        _, regex = make_log_format_regex(log_format)
        log_keys = []
        for line in sys.stdin.readlines():
            # noinspection PyBroadException,PyUnusedLocal
            try:
                line = re.sub(r'[^\x00-\x7F]+', '<NASCII>', line.strip())
                match = regex.search(line)
                process = match.group('process') if 'process' in match.groups() else None
                content = match.group('content')
                seq = re.split(r'\s+', content)  # compute before preprocess

                # handle defanged indicators of compromise
                content, params1 = ioc_parse(content)

                # catch the rest
                content, params2 = preprocess(content, REGEXS)

                params = params1 + params2

                ps = []
                for p in params:
                    ps.append({
                        'char_start': p[0],
                        'char_end': p[1],
                        'token_start': p[4],
                        'token_end': p[5],
                        'entity': p[3],
                        'value': p[2]
                    })

                # TODO include the refanged value if present

                # extract entities using NLP
                # I'm not expecting anything from the out-of-the-box model
                # it must be trained using domain-specific data.
                doc = nlp(content)
                for ent in doc.ents:
                    ps.append({
                        'char_start': ent.start_char,
                        'char_end': ent.end_char,
                        'token_start': ent.start,
                        'token_end': ent.end,
                        'entity': ent.label,
                        'value': ent.text
                    })

                obj = slm.insert(content)
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
                # for j, p in enumerate(ps):
                #     p['pos'] = j

                # print('{}\t{}\t{}\t{}\t{}\t{}'.format(line, process, obj.lcsseq(), obj.getobjid(),
                #                                       obj.param(content), json.dumps(ps)))
                log_id = hashlib.md5((content + str(datetime.now())).encode('utf-8')).hexdigest()[0:8]
                metadata = {
                    'process': process
                }
                log_key = obj.lcsseq()
                if log_key not in log_keys:
                    log_keys.append(log_key)

                print(json.dumps({
                    'log_id': log_id,
                    'line': line,
                    'message': ' '.join(seq),
                    'metadata': metadata,
                    'log_key': log_key,
                    'event_id': obj.getobjid(),
                    'params': ps
                }))
            except Exception as e:
                pass

        # TODO write log keys periodically
        # with open(os.path.join(root_dir, 'Spell_result/log_keys.txt'), 'w') as f:
        with open(os.path.join(os.getenv('OUTPUT_DIR'), 'log_keys.txt'), 'w') as f:
            f.write('\n'.join(log_keys))

    else:
        tau = constants['tau'] or 0.5
        output_dir = constants['output_dir'] or 'Spell_result/'
        log_parser = LogParser(constants['log_dir'], constants['filename'], output_dir, log_format, tau, REGEXS)
        log_parser.parse(constants['filename'])


if __name__ == '__main__':
    # read args
    parser = ArgumentParser(description='Run Spell parser')
    parser.add_argument('--in-dir', dest='log_dir', type=str, help='log directory')
    parser.add_argument('--filename', dest='filename', type=str, help='log file')
    parser.add_argument('--out-dir', dest='output_dir', type=str, help='output directory')
    parser.add_argument('--log-format', dest='log_format', type=str, help='log format')
    parser.add_argument('--tau', dest='tau', type=float, help='tau')
    # parser.add_argument('--regexs', dest='regexs', type=str, help='regular expressions')
    parser.add_argument('--stream', dest='is_stream', help='set streaming mode', action='store_true')
    parser.set_defaults(is_stream=False)
    args = parser.parse_args()

    run(vars(args))
