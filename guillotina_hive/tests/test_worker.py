import json

from guillotina import app_settings
from guillotina_hive.commands.worker import WorkerCommand
from guillotina_hive.tests.tasks import TESTING_OBJECT


def test_run_task_function(command_arguments, container_command):
    """
    guillotina hive-worker --task
    """
    payload = '{"name":"random-task","task_uri":"","function":"guillotina_hive.tests.tasks.local_memory","args":{"number_one":2},"_envs":{},"persistent":false,"_image":"","_command":[],"_cpu_limit":0.0,"_mem_limit":0.0,"_container_args":{}}'  # noqa
    command_arguments.payload = payload
    command_arguments.task_id = None
    command_arguments.tags = []
    wc = WorkerCommand(command_arguments)
    TESTING_OBJECT['value'] == 0
    wc.run_command(settings=container_command['settings'])
    assert TESTING_OBJECT['value'] == 2


def test_run_task_name(command_arguments, container_command):
    """
    guillotina hive-worker --task
    """
    payload = '{"name":"calculate-numbers","task_uri":"","function":"","args":{"number_one":2,"number_two":2},"_envs":{},"persistent":false,"_image":"","_command":[],"_cpu_limit":0.0,"_mem_limit":0.0,"_container_args":{}}'  # noqa
    command_arguments.payload = payload
    command_arguments.task_id = None
    command_arguments.tags = []
    wc = WorkerCommand(command_arguments)
    wc.run_command(settings=container_command['settings'])


async def test_run_task_uri_noresult(command_arguments, hive_requester):
    async with hive_requester as requester:
        resp, status = await requester(
            'POST',
            '/db/guillotina/+tasks',
            data=json.dumps({
                "@type": "Task",
                "id": "calculate-numbers"
            })
        )

        assert status == 201

        resp, status = await requester(
            'POST',
            '/db/guillotina/+tasks/calculate-numbers',
            data=json.dumps({
                "@type": "Execution",
                "params": {
                    "number_one": 2,
                    "number_two": 2
                }
            })
        )

        assert status == 201

        command_arguments.task_id = '/db/guillotina/+tasks/calculate-numbers/' + \
            resp['@name']
        command_arguments.tags = []
        wc = WorkerCommand(command_arguments)
        result = await wc.run(command_arguments, app_settings, None)
        assert result == 4


async def test_run_task_uri_result(command_arguments, hive_requester):
    async with hive_requester as requester:
        resp, status = await requester(
            'POST',
            '/db/guillotina/+tasks',
            data=json.dumps({
                "@type": "Task",
                "id": "local-memory"
            })
        )

        assert status == 201

        resp, status = await requester(
            'POST',
            '/db/guillotina/+tasks/local-memory',
            data=json.dumps({
                "@type": "Execution",
                "params": {
                    "number_one": 2
                }
            })
        )

        assert status == 201

        command_arguments.task_id = '/db/guillotina/+tasks/local-memory/' + resp['@name']  # noqa
        command_arguments.tags = []
        wc = WorkerCommand(command_arguments)
        TESTING_OBJECT['value'] == 0

        await wc.run(
            command_arguments,
            app_settings,
            None)
        assert TESTING_OBJECT['value'] == 2
