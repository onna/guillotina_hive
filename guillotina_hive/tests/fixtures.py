import logging
import os

from aioclustermanager.tests.utils import get_k8s_config
import docker
from guillotina import testing
from guillotina.component import get_utility
from guillotina_hive.interfaces import IHiveClientUtility
from guillotina_hive.tests.utils import HiveRequesterAsyncContextManager

import pytest

IMAGE_NAME = 'hive_test_image'


def base_settings_configurator(settings):
    if 'applications' in settings:
        settings['applications'].append('guillotina_hive')
    else:
        settings['applications'] = ['guillotina_hive']

    if 'hive_tasks' not in settings:
        settings['hive_tasks'] = {}

    settings['hive_tasks'].update({
        'calculate-numbers': 'guillotina_hive.tests.tasks.calculate_numbers',
        'with-args': 'guillotina_hive.tests.tasks.task_with_all_args',
        'missing-task-func': 'foobar',
        'slow-task': 'guillotina_hive.tests.tasks.slow_task',
        'local-memory': 'guillotina_hive.tests.tasks.local_memory',
        'compute': 'guillotina_hive.tests.tasks.compute'
    })
    settings['hive'] = {
        "image": local_hive_image(),
        "orchestrator": "k8s",
        "namespace": "hivetest",
        "master": True,
        "cluster_config": get_k8s_config()
    }


testing.configure_with(base_settings_configurator)
logger = logging.getLogger('guillotina_hive')

BUILDED_IMAGE = False


@pytest.fixture(scope='function')
def local_hive_image():
    global BUILDED_IMAGE
    if 'TEST_HIVE_IMAGE' not in os.environ:
        if BUILDED_IMAGE is False:
            logger.warning('Image build')
            docker_client = docker.from_env(version='1.23')
            docker_client.images.build(
                path='/'.join(os.path.realpath(__file__).split('/')[:-3]),
                tag=IMAGE_NAME
            )
        BUILDED_IMAGE = True
        return IMAGE_NAME
    else:
        return os.environ['TEST_HIVE_IMAGE']


@pytest.fixture(scope='function')
async def hive_requester(guillotina):
    return HiveRequesterAsyncContextManager(guillotina)


@pytest.fixture(scope='function')
async def hive_requester_k8s(guillotina, k8s_config, local_hive_image):
    async with HiveRequesterAsyncContextManager(guillotina) as guillotina:
        hive = get_utility(IHiveClientUtility)
        await hive.cm.cleanup_jobs(hive.ns)
        yield guillotina


@pytest.fixture(scope='function')
async def hive_requester_nomad(guillotina, nomad_config, local_hive_image):
    hive = get_utility(IHiveClientUtility)
    hive._cluster_environment = nomad_config
    hive._image = local_hive_image
    await hive.config()
    await hive.cm.cleanup_jobs(hive.ns)
    return HiveRequesterAsyncContextManager(guillotina)
