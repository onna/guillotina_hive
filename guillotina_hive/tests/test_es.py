import asyncio
import json

from guillotina import app_settings
from guillotina.component import get_utility
from guillotina.interfaces import ICatalogUtility
from guillotina.tests.utils import get_mocked_request
from guillotina.tests.utils import get_root
try:
    from guillotina_elasticsearch.reindex import Reindexer
except ImportError:
    Reindexer = object()
from guillotina_hive.commands.worker import WorkerCommand
from guillotina_hive.model.task import Task
from guillotina_hive.utils import get_full_content_path


async def test_reindex_es(es_requester, command_arguments):
    async with es_requester as requester:
        resp, status = await requester(
            'POST',
            '/db/guillotina/',
            data=json.dumps({
                '@type': 'Folder',
                'title': 'Folder',
                'id': 'folder'
            })
        )
        assert status == 201
        resp, status = await requester(
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
        txn = await request._tm.begin(request)
        container = await root.async_get('guillotina')
        request.container = container

        search = get_utility(ICatalogUtility)
        reindexer = Reindexer(search, container, full=True)
        await asyncio.sleep(1)
        await search.refresh(container)
        index_name = await search.get_index_name(container)
        await search.unindex_all_children(container, index_name)
        await asyncio.sleep(1)
        await search.refresh(container)
        uids = await reindexer.get_all_uids()

        await reindexer.reindex(container)
        await asyncio.sleep(1)
        await search.refresh(container)
        uids = await reindexer.get_all_uids()
        assert len(uids) > 1

        await search.unindex_all_children(container, index_name)

        task_info = Task(data={
            "name": 'es-reindex',
            "guillotina": True,
            "args": {
                "path": get_full_content_path(request, container),
            }
        })

        command_arguments.payload = task_info.serialize()
        command_arguments.task_id = None
        command_arguments.tags = []
        wc = WorkerCommand(command_arguments)
        await wc.run(command_arguments, app_settings, None)

        await asyncio.sleep(1)
        await search.refresh(container)
        uids = await reindexer.get_all_uids()
        assert len(uids) > 1

        await request._tm.abort(txn=txn)
