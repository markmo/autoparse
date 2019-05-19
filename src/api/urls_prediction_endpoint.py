import logging
import os
from pathlib import Path

import falcon

from ml.url_classifier.bilstm import BiLstmPredictor

ROOT = Path(__file__).parent.parent.parent


class UrlsResource(object):

    def __init__(self):
        model_path = ROOT / os.getenv('MODELS_DIR')
        self.predictor = BiLstmPredictor()
        self.predictor.load_model(model_path)
        logging.info('Model initialized!')

    def on_post(self, req, resp):
        logging.debug('-> ' + self.on_post.__name__)
        url = req.stream.read().decode('utf-8')
        logging.debug('URL: ' + url)
        if len(url) == 0:
            raise falcon.HTTPBadRequest(
                'Missing URL',
                'A URL must be submitted in the request body.')

        pred = self.predictor.predict(url)
        resp.status = falcon.HTTP_200
        resp.body = 'bad' if pred == 1 else 'good'
