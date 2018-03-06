from flask import Flask
import socket
import logging

logger = logging.getLogger(__name__)
app = Flask(__name__)


@app.route('/')
def index_page():
    logger.info('GET /')
    return 'Hello from {}, version 2.0'.format(socket.gethostname())
