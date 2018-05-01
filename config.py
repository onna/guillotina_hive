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

logger.warning("Defined tasks")
for k, v in tasks.items():
    logger.warning("%s: %s" % (k, v))


if 'APP_SETTINGS' in os.environ:
    settings = json.loads(base64.b64decode(os.environ['APP_SETTINGS']))
    configuration.update(settings)

configuration['hive_tasks'] = tasks

with open('config.json', 'w') as f:
    f.write(json.dumps(configuration))
