from logging.config import dictConfig

import falcon

from api.config import LOGGING_CONFIG
from api.logs_endpoint import LogsResource
from api.urls_prediction_endpoint import UrlsResource

dictConfig(LOGGING_CONFIG)

app = falcon.API()
logs = LogsResource()
urls = UrlsResource()

app.add_route('/logs', logs)
app.add_route('/urls', urls)
