import json

from guillotina import app_settings
from guillotina.tests.utils import get_mocked_request
from guillotina.tests.utils import get_root
from guillotina_hive.commands.worker import WorkerCommand
from guillotina_hive.utils import create_apply_task


class ElephantApply:
    '''
    apply func that keeps track of what was done on it
    '''

    def __init__(self):
        self.calls = []

    def __call__(self, *args, **kwargs):
        self.calls.append({
            'args': args,
            'kwargs': kwargs
        })


apply_function = ElephantApply()
apply_function.__name__ = 'apply_function'


async def test_apply_recursive(command_arguments, hive_requester):
    async with hive_requester as requester:
        _, status = await requester(
            'POST',
            '/db/guillotina/',
            data=json.dumps({
                '@type': 'Folder',
                'title': 'Folder',
                'id': 'folder'
            })
        )
        assert status == 201
        _, status = await requester(
            'POST',
            '/db/guillotina/folder',
            data=json.dumps({
                '@type': 'Item',
                'title': 'Item',
                'id': 'item'
            })
        )
        assert status == 201

        request = get_mocked_request(requester.db)
        root = await get_root(request)
        await request._tm.begin(request)
        container = await root.async_get('guillotina')
        request.container = container

        # now do it with tasks...
        apply_function.__class__.__name__ = 'apply_function'  # to dump func
        task = create_apply_task(
            'apply-recursive', container, apply_function, request)

        command_arguments.payload = task.serialize()
        command_arguments.task_id = None
        command_arguments.tags = []
        wc = WorkerCommand(command_arguments)
        await wc.run(command_arguments, app_settings, None)
        assert len(apply_function.calls) == 4
        assert apply_function.calls[0]['args'][0]._p_oid == container._p_oid
