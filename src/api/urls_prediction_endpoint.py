from pathlib import Path
import os

import falcon

from ml.bilstm import BiLstmPredictor
import settings

ROOT = Path(__file__).parent.parent.parent


class UrlsResource(object):

    def __init__(self):
        model_path = ROOT / os.getenv('MODELS_DIR')
        self.predictor = BiLstmPredictor()
        self.predictor.load_model(model_path)

    def on_get(self, req, resp, url):
        pred = self.predictor.predict(url)
        resp.status = falcon.HTTP_200
        resp.body = 'bad' if pred == 1 else 'good'


