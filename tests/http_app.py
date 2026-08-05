from __future__ import annotations

import ssl
import time

import flask
from flask import request

app = flask.Flask(__name__)


@app.route("/ip")
def ip() -> str:
    return request.remote_addr  # type:ignore[return-value]


@app.route("/delay/<int:seconds>")
def delay(seconds: float) -> str:
    time.sleep(seconds)
    return "ok"


def run_app(
    host: str,
    port: int,
    certfile: str | None = None,
    keyfile: str | None = None,
) -> None:
    if certfile and keyfile:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        ssl_context.load_cert_chain(certfile, keyfile)
    else:
        ssl_context = None

    print(f"Starting http server on {host}:{port}...")
    app.run(debug=False, host=host, port=port, threaded=True, ssl_context=ssl_context)
