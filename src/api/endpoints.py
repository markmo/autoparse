import falcon

from api.logs_endpoint import LogsResource
from api.urls_prediction_endpoint import UrlsResource


app = falcon.API()
logs = LogsResource()
urls = UrlsResource()

app.add_route('/logs', logs)
app.add_route('/urls/{url}', urls)
