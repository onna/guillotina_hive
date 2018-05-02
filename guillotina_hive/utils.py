from datetime import datetime
from guillotina import app_settings
from guillotina.component import get_utility
from guillotina.interfaces import IAbsoluteURL
from guillotina.interfaces.security import PermissionSetting
from guillotina.utils import get_content_path
from guillotina.utils import get_current_request
from guillotina.utils import get_dotted_name
from guillotina_hive.interfaces import IHiveClientUtility
from zope.interface.interface import InterfaceClass

import json


def get_full_content_path(request, ob):
    path = '/'
    if hasattr(request, '_db_id'):
        path += request._db_id + '/'
    if hasattr(request, 'container'):
        path += request.container.__name__ + '/'
    return '{}{}'.format(path, get_content_path(ob)).replace('//', '/').rstrip('/')  # noqa


class GuillotinaConfigJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, complex):
            return [obj.real, obj.imag]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, type):
            return obj.__module__ + '.' + obj.__name__
        elif isinstance(obj, InterfaceClass):
            return obj.__identifier__  # noqa
        try:
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)

        if isinstance(obj, PermissionSetting):
            return obj.get_name()
        if callable(obj):
            return obj.__module__ + '.' + obj.__name__
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


def create_apply_task(name, ob, function, request=None, commit=False,
                      args=None, kwargs=None, task_config=None):
    if task_config is None:
        task_config = {}
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    from guillotina_hive.model.task import Task

    if request is None:
        request = get_current_request()

    user_data = {}
    try:
        participation = request.security.participations[0]
        user = participation.principal
        user_data = {
            'id': user.id,
            'roles': user.roles,
            'groups': user.groups,
            'Authorization': request.headers.get('Authorization'),
            'data': getattr(user, 'data', {})
        }
    except (AttributeError, IndexError):
        pass

    if request.container:
        user_data['container_url'] = IAbsoluteURL(request.container, request)()

    data = {
        "name": name,
        "guillotina": True,
        "args": {
            "path": get_full_content_path(request, ob),
            "function": get_dotted_name(function),
            'commit': commit,
            'args': args,
            'kwargs': kwargs,
            'user_data': user_data
        }
    }
    data.update(task_config)
    task_info = Task(data=data)
    return task_info


async def add_apply_recursive_task(*args, **kwargs):
    hive = get_utility(IHiveClientUtility)
    task_info = create_apply_task('apply-recursive', *args, **kwargs)
    await hive.run_task(task_info)
    return task_info


async def add_object_task(*args, **kwargs):
    hive = get_utility(IHiveClientUtility)
    task_info = create_apply_task('apply-object', *args, **kwargs)
    await hive.run_task(task_info)
    return task_info


def settings_serializer():
    settings = {}

    for key in ('elasticsearch', 'redis', 'root_user', 'applications',
                'databases', 'hive', 'utilities'):
        if key in app_settings:
            settings[key] = app_settings[key]

    return settings
