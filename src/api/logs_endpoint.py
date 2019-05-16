import falcon
import os
from pathlib import Path
import subprocess

import settings

ROOT = Path(__file__).parent.parent


class LogsResource(object):

    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.body = 'autoparse logs api is running'

    def on_post(self, req, resp):
        # TODO run a new thread to not block response
        read = subprocess.Popen(['python', f'{ROOT}/read_from_es.py', '--stream', '--maxlines', '-1'],
                                stdout=subprocess.PIPE)
        parse = subprocess.Popen(['python', f'{ROOT}/parse.py', '--stream', '--log-format', '<content>'],
                                 stdin=read.stdout, stdout=subprocess.PIPE)
        end_of_pipe = parse.stdout

        with open('{}/output.jsonl'.format(os.getenv('OUTPUT_DIR')), 'w') as f:
            for line in end_of_pipe:
                f.write(line.decode('utf-8'))

        resp.status = falcon.HTTP_200
        resp.body = 'OK'


app = falcon.API()
logs = LogsResource()

app.add_route('/logs', logs)
