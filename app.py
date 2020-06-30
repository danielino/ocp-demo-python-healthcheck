import datetime
import sys
import os
import structlog
import logging
import redis
import random
from flask import Flask, jsonify

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
    context_class=structlog.threadlocal.wrap_dict(dict),
)

logger = structlog.get_logger()

# disable log message from flask
logging.getLogger("werkzeug").setLevel(logging.ERROR)
os.environ["WERKZEUG_RUN_MAIN"] = "true"


def get_redis_connection():
    if not REDIS_PASSWORD:
        return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DATABASE)
    return redis.Redis(
        host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DATABASE, password=REDIS_PASSWORD
    )


app = Flask(__name__)


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
    return jsonify({"context": "/hello", "time": datetime.datetime.now().isoformat()})


@app.route("/health/liveness")
def liveness():
    logger.debug("liveness", status="ok")
    return jsonify({"status": "ok"}), 200


@app.route("/health/readiness")
def readiness():
    try:
        r = get_redis_connection()
        r.ping()
        redis_alive = True
        logger.debug("readiness", status="ok")
        return jsonify({"status": "ok", "redis_alive": redis_alive}), 200

    except:
        redis_alive = False
    logger.error("readiness", status="ko")
    return jsonify({"status": "ok", "redis_alive": redis_alive}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
