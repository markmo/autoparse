from argparse import ArgumentParser
from datetime import datetime
import hashlib
import json
import os
import re
from spell import LogParser
from spell_stream import get_span, LCSMap, make_log_format_regex, preprocess
import sys


# noinspection SpellCheckingInspection
def run(constants):
    # root_dir = os.path.dirname(__file__)
    regexs = {
        'uri': r'/(?!(dev|proc))([\w\.]+/)+\w+\.php',
        'url': r'https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)',
        'email': r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
        'device': r'/dev(/[\w\.]+)+',
        'process': r'/proc(/[\w\.]+)+',
        'ip_address': r'(tcp/)?([0-9]{1,3}\.){3}[0-9]{1,3}((\+[0-9]{1,3})|:[0-9]{1,5})?',
        'memory_address': r'0x[a-zA-Z0-9]+((-|\s)[a-zA-Z0-9]+)?',
        'uuid': r'\b[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-\b[0-9a-fA-F]{12}\b',
        'memory_k': r'\b\d+[kK][bB]?\b',
        'disk_mb': r'\b\d+[mM][bB]?\b',
        'disk_gb': r'\b\d+[gG][bB]?\b',
        'clock_speed': r'\b\d+(\.\d+)?GHz\b',
        # put these last
        'file': r'/(?!(dev|proc))([\w\.]+/)+\w+(?!\.php)(\.\w+)?',
        'version': r'\b[vV]?\d+(\.\d+)+(-[0-9a-zA-Z]+)?\b',
        'number': r'\b(?<=\s)\d+(?=\s)\b',
    }
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
                process = match.group('process')
                content = match.group('content')
                seq = re.split(r'\s+', content)  # compute before preprocess
                content, params = preprocess(content, regexs)
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
                # raise e
                pass

        # with open(os.path.join(root_dir, 'Spell_result/log_keys.txt'), 'w') as f:
        with open(os.path.join('/Users/d777710/src/cybersecurity/output', 'log_keys.txt'), 'w') as f:
            f.write('\n'.join(log_keys))

    else:
        tau = constants['tau'] or 0.5
        output_dir = constants['output_dir'] or 'Spell_result/'
        log_parser = LogParser(constants['log_dir'], constants['filename'], output_dir, log_format, tau, regexs)
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
