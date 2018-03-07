import socket
import logging
import os
import hmac

from flask import Flask, request, Response
from flask_redis import FlaskRedis
from redis.exceptions import RedisError
from prometheus_client import Counter, generate_latest

HOST_COUNTER = 'host_counts'
COUNT = Counter('request_count', 'App request count', ['method', 'endpoint', 'http_status'])

logger = logging.getLogger(__name__)
app = Flask(__name__)

app.config['REDIS_URL'] = os.environ['REDIS_URL']
redis_store = FlaskRedis(app)


@app.after_request
def after_request(response):
    COUNT.labels(request.method, request.endpoint, response.status_code).inc()
    return response


@app.route('/')
def index_page():
    logger.info('GET /')
    pipe = redis_store.pipeline()
    pipe.hincrby(HOST_COUNTER, socket.gethostname())
    pipe.hgetall(HOST_COUNTER)
    result = pipe.execute()
    return '\n'.join(['{}: {}'.format(k.decode(), v.decode()) for k, v in result[1].items()])


@app.route('/reset')
def reset():
    auth = request.authorization
    if not auth or not hmac.compare_digest('{}:{}'.format(auth.username, auth.password), os.environ.get('AUTH', '')):
        return Response('Not authenticated', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
    redis_store.delete(HOST_COUNTER)
    return 'ok'


@app.route('/health')
def health_check():
    try:
        redis_store.ping()
    except RedisError:
        return 'Redis not available', 500
    return 'ok'


@app.route('/metrics')
def metrics():
    return generate_latest()
