# Basic script to define the guillotina_hive configuration to connect to
# external services
# We assume there is a DB_CONFIG env var with a configuration to generate

import os
import json
import base64

import logging
logger = logging.getLogger('guillotina_hive')

with open('config.json', 'r') as f:
    configuration = json.loads(f.read())

try:
    with open('tasks.json', 'r') as f:
        tasks = json.loads(f.read())
except FileNotFoundError:
    tasks = {}

logger.warn("Defined tasks")
for k, v in tasks.items():
    logger.warn("%s: %s" % (k, v))


if 'DB_CONFIG' in os.environ:
    db_config = json.loads(base64.b64decode(os.environ['DB_CONFIG']))
    configuration['databases'] = db_config

try:
    import guillotina_elasticsearch  # noqa
    ES_INSTALLED = True
except ImportError:
    ES_INSTALLED = False

if ES_INSTALLED and 'ES_CONFIG' in os.environ:
    es_config = json.loads(base64.b64decode(os.environ['ES_CONFIG']))
    configuration['elasticsearch'] = es_config
    configuration['applications'].append('guillotina_elasticsearch')


try:
    import guillotina_redis  # noqa
    REDIS_INSTALLED = True
except ImportError:
    REDIS_INSTALLED = False

if REDIS_INSTALLED and 'REDIS_CONFIG' in os.environ:
    redis_config = json.loads(base64.b64decode(os.environ['REDIS_CONFIG']))
    configuration['redis'] = redis_config
    configuration['applications'].append('guillotina_redis')


try:
    import guillotina_gcloudstorage  # noqa
    GCLOUD_INSTALLED = True
except ImportError:
    GCLOUD_INSTALLED = False

if GCLOUD_INSTALLED and 'GCLOUD_CONFIG' in os.environ:
    gcloud_config = json.loads(base64.b64decode(os.environ['GCLOUD_CONFIG']))
    configuration['utilities'].append({
        "provides": "guillotina_gcloudstorage.interfaces.IGCloudBlobStore",
        "factory": "guillotina_gcloudstorage.storage.GCloudBlobStore",
        "settings": gcloud_config
    })
    configuration['applications'].append('guillotina_gcloudstorage')

try:
    import guillotina_s3storage  # noqa
    S3_INSTALLED = True
except ImportError:
    S3_INSTALLED = False

if S3_INSTALLED and 'S3_CONFIG' in os.environ:
    s3_config = json.loads(base64.b64decode(os.environ['S3_CONFIG']))
    configuration['utilities'].append({
        "provides": "guillotina_s3storage.interfaces.IS3BlobStore",
        "factory": "guillotina_s3storage.storage.S3BlobStore",
        "settings": s3_config
    })
    configuration['applications'].append('guillotina_s3storage')

configuration['hive_tasks'] = tasks

with open('config.json', 'w') as f:
    f.write(json.dumps(configuration))
