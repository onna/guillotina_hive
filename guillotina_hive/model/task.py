from guillotina import app_settings
from guillotina.utils import lazy_apply
from guillotina.utils import resolve_dotted_name
from guillotina_hive.exceptions import NoTaskFunctionFoundError
from guillotina_hive.exceptions import NoTaskFunctionValidError
from guillotina_hive.utils import GuillotinaConfigJSONEncoder

import asyncio
import base64
import json
import jsonschema
import logging
import ujson
import uuid


logger = logging.getLogger('guillotina_hive')


TASK_SCHEMA = {
    'type': 'object',
    'properties': {
        'name': {
            'type': 'string',
            'pattern': '^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'},
        'id': {'type': 'string'},
        'task_uri': {'type': 'string'},
        'function': {'type': 'string'},
        'args': {'type': 'object'},
        'persistent': {'type': 'boolean'},
        'guillotina': {'type': 'boolean'},
        '_namespace': {'type': 'string'},
        '_envs': {'type': 'object'},
        '_image': {'type': 'string'},
        '_command': {'type': 'array'},
        '_cpu_limit': {'type': 'number'},
        '_mem_limit': {'type': 'number'},
        '_container_args': {'type': 'object'}
    }
}


class Task:
    name = id = function = None
    args = {}
    persistent = False
    guillotina = True
    _namespace = _command = _image = task_uri = None
    _container_args = {}
    _cpu_limit = _mem_limit = 0.0
    _envs = {}

    def __init__(self, data=None, base_image=None):
        if data is not None:
            for key in TASK_SCHEMA['properties']:
                if key not in data:
                    if TASK_SCHEMA['properties'][key]['type'] == 'string':
                        data[key] = ""
                    elif TASK_SCHEMA['properties'][key]['type'] == 'object':
                        data[key] = {}
                    elif TASK_SCHEMA['properties'][key]['type'] == 'boolean':
                        data[key] = False
                    elif TASK_SCHEMA['properties'][key]['type'] == 'array':
                        data[key] = []
                    elif TASK_SCHEMA['properties'][key]['type'] == 'number':
                        data[key] = 0.0
            jsonschema.validate(data, TASK_SCHEMA)
            self.__dict__.update(data)
        if base_image is not None:
            self._base_image = base_image
        else:
            self._base_image = None
        if not self.id:
            self.id = self.name + uuid.uuid4().hex[:6]

    def serialize(self):
        result = {}
        for key in TASK_SCHEMA['properties']:
            result[key] = getattr(self, key, None)
        jsonschema.validate(result, TASK_SCHEMA)
        return ujson.dumps(result)  # pylint: disable=I1101

    async def run(self, request, tags, root):
        # Look for the function that we want to execute
        if self.name not in app_settings['hive_tasks'] and \
                self.function == "" and \
                self._command == "":
            # We did not found the function
            raise NoTaskFunctionFoundError(self.name)
        elif self.name in app_settings['hive_tasks'] and self.function == "":
            # Its a registered task so we load the function
            self.function = app_settings['hive_tasks'][self.name]

        try:
            # Check the defined function exist
            if isinstance(self.function, dict):
                logger.warning(f'Running : {self.function["name"]}')
                func = self.function['klass']
            else:
                logger.warning(f'Running : {self.function}')
                func = resolve_dotted_name(self.function)
        except ModuleNotFoundError:
            raise NoTaskFunctionFoundError(self.name)
        except ValueError:
            raise NoTaskFunctionFoundError(self.name)

        logger.warning(f'Running task {self.name}({self.task_uri})')

        if asyncio.iscoroutinefunction(func):
            # Its an async function
            result = await lazy_apply(
                func, request=request, tags=tags,
                root=root, **self.args)
        else:
            # Its a non compute and non async task, its not valid
            raise NoTaskFunctionValidError(self.name)

        if self.persistent:
            # TODO (ramon): we need to store the result on the execution
            pass
        return result

    @property
    def command(self):
        if len(self._command) == 0:
            return None
        else:
            return self._command

    @property
    def container_args(self):
        if len(self._container_args) == 0:
            return app_settings['hive']['guillotina_default']['container_args']
        else:
            return [
                "--%s%s" % (
                    key,
                    '=' + value if value is not None else '')
                for key, value in self._container_args]

    @property
    def mem_limit(self):
        if self._mem_limit == 0.0:
            limit = 1.0
        else:
            limit = self._mem_limit
        memory = limit * 1000
        memory = "%dM" % memory
        return memory

    @property
    def cpu_limit(self):
        if self._cpu_limit == 0.0:
            limit = 0.7
        else:
            limit = self._cpu_limit
        cpu = limit * 1000
        cpu = "%dm" % cpu
        return cpu

    @property
    def envs(self):
        # if its a function task get the payload for task
        result = {}
        if self.persistent != '':
            result = {
                'PAYLOAD': self.serialize()
            }

        if self.guillotina:
            serializer = resolve_dotted_name(
                app_settings['hive']['settings_serializer'])
            settings = serializer()
            result['APP_SETTINGS'] = base64.b64encode(
                json.dumps(
                    settings,
                    cls=GuillotinaConfigJSONEncoder,
                    ensure_ascii=False
                ).encode('utf-8')).decode('utf-8')

        if len(self._envs.keys()) > 0:
            result.update(self._envs)
        return result

    @property
    def image(self):
        if self._image == "":
            return self._base_image
        return self._image

    @property
    def volumes(self):
        if self.guillotina:
            return app_settings['hive']['guillotina_default']['volumes']

    @property
    def volumeMounts(self):
        if self.guillotina:
            return app_settings['hive']['guillotina_default']['volumeMounts']

    @property
    def envFrom(self):
        if self.guillotina:
            return app_settings['hive']['guillotina_default']['envFrom']

    @property
    def entrypoint(self):
        if self.guillotina:
            return app_settings['hive']['guillotina_default']['entrypoint']

    @property
    def namespace(self):
        return self._namespace
