import datetime
import sys
import os
import structlog
import logging
import redis
import random
from flask import Flask, jsonify
from flask_redis import FlaskRedis

REDIS_HOST = os.environ.get("REDIS_SERVICE_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_SERVICE_PORT", "6379"))
REDIS_DATABASE = os.environ.get("REDIS_DATABASE", "0")
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", None)

DEBUG = os.environ.get("DEBUG", False)


def timestamper(_, __, event_dict):
    event_dict["time"] = datetime.datetime.now().isoformat()
    return event_dict


logging.basicConfig(
    format="%(message)s", level=logging.DEBUG if DEBUG else logging.INFO
)

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        timestamper,
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# disable log message from flask
logging.getLogger("werkzeug").setLevel(logging.ERROR)

REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DATABASE}"

app = Flask(__name__)
app.config["REDIS_URL"] = REDIS_URL
redis_client = FlaskRedis(app)

def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)


@app.route("/")
def index():
    logger.info("http_request", context="/")
    return jsonify({"context": "/", "method": "index"})


@app.route("/random")
def _random():
    logger.info("http_request", context="/random")
    return jsonify({"number": random.randint(0, 100000)})


@app.route("/hello")
def hello():
    logger.info("http_request", context="/hello")
    return jsonify({"context": "/hello", "time": datetime.datetime.now().isoformat()})


@app.route("/quicksort/<string:params>")
def quicksort_api(params: str):
    r = quicksort([int(x) for x in params.split(",")])
    return jsonify({"response": r})

@app.route("/stress")
def stress():
    logger.info("http_request", context="/stress")
    i = 0
    c = 10
    while i < (2 << 20): # 2097152
        i += 1
        var = (i // 100) ** c
    return jsonify({"context" : "/stress", "result": i})
        


@app.route("/health/liveness")
def liveness():
    logger.debug("liveness", status="ok")
    return jsonify({"status": "ok"}), 200


@app.route("/health/readiness")
def readiness():
    try:
        redis_alive = redis_client.ping()
        logger.debug("readiness", status="ok")
        return jsonify({"status": "ok", "redis_alive": redis_alive}), 200

    except Exception as e:
        logger.exception(e)
        redis_alive = False
    logger.error("readiness", status="ko")
    return jsonify({"status": "ko", "redis_alive": redis_alive}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=DEBUG)
