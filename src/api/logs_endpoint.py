import os
from pathlib import Path
from subprocess import PIPE, Popen
from threading import Thread

import falcon

import settings

ROOT = Path(__file__).parent.parent


class LogsResource(object):

    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.body = 'autoparse logs api is running'

    def on_post(self, req, resp):
        """ TODO find a cleaner alternative """
        read = Popen(['python', f'{ROOT}/read_from_es.py', '--stream', '--maxlines', '-1'], stdout=PIPE)
        parse = Popen(['python', f'{ROOT}/parse.py', '--stream', '--log-format', '<content>'],
                      stdin=read.stdout, stdout=PIPE, stderr=PIPE)
        log_lines = parse.stdout
        log_keys = parse.stderr  # TODO hack to capture two outputs from `parse`
        output_dir = os.getenv('OUTPUT_DIR')
        log_lines_out_path = f'{output_dir}/log_lines.jsonl'
        log_keys_out_path = f'{output_dir}/log_keys.txt'

        # don't block
        Thread(target=self._write_output, args=(log_lines_out_path, log_lines)).start()
        Thread(target=self._write_output, args=(log_keys_out_path, log_keys)).start()

        resp.status = falcon.HTTP_200
        resp.body = 'OK'

    def _write_output(self, path, lines):
        with open(path, 'w') as f:
            for line in lines:
                f.write(line.decode('utf-8'))


app = falcon.API()
logs = LogsResource()

app.add_route('/logs', logs)
