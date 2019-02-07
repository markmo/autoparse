from argparse import ArgumentParser
from spell import LogParser
from spell_stream import LCSMap
import sys


def run(constants):
    if constants['is_stream']:
        slm = LCSMap(r'\s+')
        for line in sys.stdin.readlines():
            line = line.strip('\n')
            obj = slm.insert(line)
            print(obj.getobjid(), obj.param(line))
    else:
        regexs = {
            'file': r'/(?!dev)([\w\.]+/)+\w+(?!\.php)\.\w+',
            'uri': r'/(?!dev)([\w\.]+/)+\w+\.php',
            'email': r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
            'device': r'/dev(/[\w\.]+)+',
            'ip_address': r'(tcp/)?([0-9]{1,3}\.){3}[0-9]{1,3}((\+[0-9]{1,3})|:[0-9]{1,5})?'
        }
        tau = constants['tau'] or 0.5
        log_format = constants['log_format'] or '<process>: <content>'
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
