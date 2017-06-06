import os
import urlparse
import bmemcached
import json

import redis
import celery
cache = bmemcached.Client(os.environ.get('MEMCACHEDCLOUD_SERVERS').split(','), os.environ.get('MEMCACHEDCLOUD_USERNAME'), os.environ.get('MEMCACHEDCLOUD_PASSWORD'))


redis_url = redis.from_url(os.environ.get("REDIS_URL"))
app.config['CELERY_BROKER_URL'] = redis_url
app.config['CELERY_RESULT_BACKEND'] = redis_url
celery = celery.Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)
