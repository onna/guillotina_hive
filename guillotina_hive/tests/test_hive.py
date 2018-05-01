import asyncio

from aioclustermanager.job import Job
from guillotina.component import get_utility
from guillotina_hive.interfaces import IHiveClientUtility
from guillotina_hive.model.task import Task
from guillotina_hive.tests.utils import reconfigure_db


async def test_install(hive_requester_k8s):
    async with hive_requester_k8s as requester:
        resp, status = await requester('GET', '/db/guillotina/+tasks')
        assert status == 200
        resp, status = await requester('GET', '/db/guillotina/@addons')
        assert status == 200
        assert 'hive' in resp['installed']


async def test_add_task_hive_non_persist(hive_requester_k8s):
    # Lets create a task from a guillotina client that is not persist
    async with hive_requester_k8s as requester:  # noqa pylint: disable=W0612

        hive = get_utility(IHiveClientUtility)
        await hive.cm.cleanup_jobs(hive.default_namespace)
        task = Task(data={
            "name": "calculate-numbers",
            "guillotina": True,
            "args": {
                "number_one": 2,
                "number_two": 2}
        })
        await reconfigure_db(hive, task)
        await hive.run_task(task)
        job = await hive.get_task_status(task.id)
        assert isinstance(job, Job)
        while job.finished is False:
            await asyncio.sleep(10)
            try:
                log = await hive.get_task_log(task.id)
                print('NEW LOG')
                print(log)
            except Exception:
                pass

            job = await hive.get_task_status(task.id)

        tries = 0
        while tries < 5:
            executions = await hive.get_task_executions(task.id)
            print(executions.statuses())
            log = await hive.get_task_log(task.id)
            print(log)
            try:
                assert executions.is_done()
                assert '4.0000' in log
                await asyncio.sleep(2)
                break
            except AssertionError:
                if tries > 4:
                    raise
                tries += 1


async def test_add_task_hive_function_non_persist(hive_requester_k8s):
    # Lets create a task from a guillotina client that is not
    # persist with function
    async with hive_requester_k8s as requester:  # noqa pylint: disable=W0612
        hive = get_utility(IHiveClientUtility)
        await hive.cm.cleanup_jobs(hive.default_namespace)
        task = Task(data={
            "name": "random-task",
            "function": "guillotina_hive.tests.tasks.calculate_numbers",
            "guillotina": True,
            "args": {
                "number_one": 2,
                "number_two": 2}
        }, base_image=hive.default_image)
        assert task.container_args == ["guillotina", "hive-worker"]
        assert task.envs['PAYLOAD'] is not None
        await reconfigure_db(hive, task)
        await hive.run_task(task)
        job = await hive.get_task_status(task.id)
        assert isinstance(job, Job)
        while job.finished is False:
            await asyncio.sleep(10)
            try:
                log = await hive.get_task_log(task.id)
                print('NEW LOG')
                print(log)
            except Exception:
                pass
            job = await hive.get_task_status(task.id)
        executions = await hive.get_task_executions(task.id)
        print(executions.statuses())
        log = await hive.get_task_log(task.id)
        print(log)
        for execution in executions:
            print('EXECUTION')
            print(execution._raw)
        assert executions.is_done()
        assert '4.0000' in log


async def test_add_task_nonhive_non_persist(hive_requester_k8s):
    # Lets create a task from a guillotina client that is not persist
    async with hive_requester_k8s as requester:  # noqa pylint: disable=W0612
        hive = get_utility(IHiveClientUtility)
        await hive.cm.cleanup_jobs(hive.default_namespace)
        task = Task(data={
            "name": "perl-task",
            "image": "perl",
            "_command": ["perl", "-Mbignum=bpi", "-wle", "print bpi(2000)"]
        }, base_image=hive.default_image)

        await hive.run_task(task)

        job = await hive.get_task_status(task.id)
        assert isinstance(job, Job)
        while job.finished is False:
            await asyncio.sleep(10)
            try:
                log = await hive.get_task_log(task.id)
                print('NEW LOG')
                print(log)
            except Exception:
                pass

            job = await hive.get_task_status(task.id)
        executions = await hive.get_task_executions(task.id)
        assert executions.is_done()
        log = await hive.get_task_log(task.id)
        assert '3.14' in log
