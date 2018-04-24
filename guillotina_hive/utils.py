from datetime import datetime
from guillotina.component import get_utility
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


async def _create_apply_task(name, ob, function, request=None, commit=False,
                             args=None, kwargs=None):
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
        user_data['id'] = user.id
        user_data['roles'] = user.roles
        user_data['groups'] = user.groups
    except (AttributeError, IndexError):
        pass

    task_info = Task(data={
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
    })
    return task_info


async def add_apply_recursive_task(*args, **kwargs):
    hive = get_utility(IHiveClientUtility)
    task_info = await _create_apply_task('apply-recursive', *args, **kwargs)
    await hive.add_task(task_info)
    return task_info


async def add_object_task(*args, **kwargs):
    hive = get_utility(IHiveClientUtility)
    task_info = await _create_apply_task('apply-object', *args, **kwargs)
    await hive.add_task(task_info)
    return task_info
