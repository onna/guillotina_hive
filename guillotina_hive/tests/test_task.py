import json

from guillotina.tests.utils import get_mocked_request
from guillotina_hive.exceptions import NoTaskFunctionFoundError
from guillotina_hive.model.task import Task

import pytest


def test_serialize_task():
    task = Task(data={
        "name": "foobar",
        "args": {
            "foo": "bar"},
        "persistent": False
    })
    task_data = json.loads(task.serialize())
    assert task_data['args'] == {'foo': 'bar'}


def test_deserialize_task():
    task = Task(data={
        "name": "foobar",
        "args": {
            "foo": "bar"},
        "persistent": False
    })
    task_data = json.loads(task.serialize())
    task2 = Task(data=task_data)

    assert task.serialize() == task2.serialize()


async def test_run_task(dummy_request):
    task = Task(data={
        "name": "calculate-numbers",
        "args": {
            "number_one": 2,
            "number_two": 2},
        "persistent": False
    })

    result = await task.run(dummy_request, None, None)
    assert result == 4


async def test_not_found_task_errors(dummy_request):
    task = Task(data={
        "name": "acalculate-numbers",
        "task_uri": "",
        "function": "",
        "args": {
            "number_one": 2,
            "number_two": 2},
        "persistent": False
    })

    with pytest.raises(NoTaskFunctionFoundError):
        await task.run(dummy_request, None, None)


async def test_not_found_task_name_errors(dummy_request):
    task = Task(data={
        "name": "acalculatenumbers",
        "task_uri": "",
        "function": "",
        "args": {
            "number_one": 2,
            "number_two": 2},
        "persistent": False
    })

    with pytest.raises(NoTaskFunctionFoundError):
        await task.run(dummy_request, None, None)


async def test_bad_task_func_errors(dummy_request):
    task = Task(data={
        "name": "acalculate-numbers",
        "task_uri": "",
        "function": "non_existing_module",
        "args": {},
        "persistent": False
    })

    with pytest.raises(NoTaskFunctionFoundError):
        await task.run(dummy_request, None, None)


async def test_compute_task(hive_requester):
    task = Task(data={
        "name": "compute",
        "compute": True,
        "persistent": False
    })
    async with hive_requester as requester:
        for i in range(10):
            resp, status = await requester(
                'POST',
                '/db/guillotina/',
                data=json.dumps({
                    "@type": "Item"
                })
            )
        request = get_mocked_request(hive_requester.guillotina.db)
        result = await task.run(request, [], hive_requester.guillotina.root)
        assert result > 0.0
