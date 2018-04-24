from guillotina import app_settings
from guillotina import configure


def load_hive_task(_context, task):
    settings = {
        'klass': task['klass']
    }

    settings.update(task['config'])
    if 'hive_tasks' not in app_settings:
        app_settings['hive_tasks'] = {}
    app_settings['hive_tasks'][task['config']['name']] = settings


configure.register_configuration_handler('hive_task', load_hive_task)  # noqa


class hive_task(configure._base_decorator):
    configuration_type = 'hive_task'


def task_registry_info(task_id):
    return app_settings['hive_tasks'].get(task_id, None)
