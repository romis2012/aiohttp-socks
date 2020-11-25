import time

import flask  # noqa
from flask import request  # noqa

app = flask.Flask(__name__)


@app.route('/ip')
def ip():
    return request.remote_addr


@app.route('/delay/<int:seconds>')
def delay(seconds):
    time.sleep(seconds)
    return 'ok'


def run_app(host, port, ssl_context=None):
    print('Starting http server on {}:{}...'.format(host, port))
    app.run(debug=False, host=host, port=port, threaded=True,
            ssl_context=ssl_context)
