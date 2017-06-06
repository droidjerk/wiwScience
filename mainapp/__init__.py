import os

import redis
import celery

from flask import Flask
from flask_bootstrap import Bootstrap
from werkzeug.contrib.cache import MemcachedCache

app = Flask(__name__)

# redis_url = redis.from_url(os.environ.get("REDIS_URL"))
# app.config['CELERY_BROKER_URL'] = redis_url
# app.config['CELERY_RESULT_BACKEND'] = redis_url
# celery = celery.Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
# celery.conf.update(app.config)

cache = MemcachedCache(['memcached-12214.c3.eu-west-1-1.ec2.cloud.redislabs.com:12214'])

Bootstrap(app)

if __name__ == '__main__':
    app.run()

from mainapp import models, views
