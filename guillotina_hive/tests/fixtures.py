from aioclustermanager.tests.utils import get_k8s_config
from guillotina import testing
from guillotina.tests import fixtures
from guillotina_hive.tests.utils import HiveRequesterAsyncContextManager

import docker
import logging
import os
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
    image = get_local_hive_image()
    settings['hive'] = {
        "default_image": image,
        "orchestrator": "k8s",
        "default_namespace": "hivetest",
        "cluster_config": get_k8s_config()
    }


testing.configure_with(base_settings_configurator)

logger = logging.getLogger('guillotina_hive')

BUILDED_IMAGE = False

DATABASE = os.environ.get('DATABASE', 'DUMMY')


@pytest.fixture(scope='session')
def db():
    """
    XXX OVERRIDE db fixture in guillotina
    detect travis, use travis's postgres; otherwise, use docker
    """
    if DATABASE == 'DUMMY':
        yield
    else:
        import pytest_docker_fixtures
        if DATABASE == 'cockroachdb':
            host, port = pytest_docker_fixtures.cockroach_image.run()
        else:
            pg_image = pytest_docker_fixtures.pg_image
            pg_image.port = 5433
            pg_image.base_image_options['publish_all_ports'] = False
            pg_image.base_image_options['ports'] = {'5432/tcp': 5433}
            host, port = pg_image.run()
            import psycopg2
            try:
                conn = psycopg2.connect(
                    f"dbname=guillotina user=postgres host={host} "
                    f"port={port}")
                cur = conn.cursor()
                cur.execute("CREATE DATABASE guillotina;")
                cur.fetchone()
                cur.close()
                conn.close()
            except Exception:  # noqa
                pass

        # mark the function with the actual host
        setattr(fixtures.get_db_settings, 'host', host)
        setattr(fixtures.get_db_settings, 'port', port)

        yield host, port  # provide the fixture value

        if DATABASE == 'cockroachdb':
            pytest_docker_fixtures.cockroach_image.stop()
        else:
            pytest_docker_fixtures.pg_image.stop()


fixtures.db = db


def get_local_hive_image():
    global BUILDED_IMAGE
    if 'TEST_HIVE_IMAGE' not in os.environ:
        if BUILDED_IMAGE is False:
            logger.warning('Image build')
            docker_client = docker.from_env(version='1.23')
            docker_client.images.build(
                path='/'.join(os.path.realpath(__file__).split('/')[:-3]),
                pull=True,
                tag=IMAGE_NAME
            )
        BUILDED_IMAGE = True
        return IMAGE_NAME
    else:
        return os.environ['TEST_HIVE_IMAGE']


@pytest.fixture(scope='function')
async def hive_requester(elasticsearch, guillotina, loop):
    return HiveRequesterAsyncContextManager(guillotina, loop)


@pytest.fixture(scope='function')
async def hive_requester_k8s(k8s_config, elasticsearch, guillotina, loop):
    return HiveRequesterAsyncContextManager(guillotina, loop)
