import asyncio
import base64
import json

from guillotina.component import get_utility
from guillotina.interfaces import ICatalogUtility
from guillotina.tests.utils import ContainerRequesterAsyncContextManager
from guillotina_hive.utils import GuillotinaConfigJSONEncoder


class HiveRequesterAsyncContextManager(ContainerRequesterAsyncContextManager):

    def __init__(self, guillotina, loop):
        super().__init__(guillotina)

        # aioes caches loop, we need to continue to reset it
        search = get_utility(ICatalogUtility)
        search.loop = loop
        if search._conn:
            search._conn.close()
        search._conn = None

    async def __aenter__(self):
        try:
            await super().__aenter__()
        except:  # noqa
            pass
        resp, status = await self.requester(
            'POST',
            '/db/guillotina/@addons',
            data=json.dumps({
                'id': 'hive'
            })
        )
        assert status == 200
        return self.requester

    async def __aexit__(self, *args):
        for task in asyncio.Task.all_tasks():
            task._log_destroy_pending = False
        return await super().__aexit__(*args)


async def reconfigure_db(hive, task):
    nodes = await hive.cm.get_nodes()
    db_config = json.loads(base64.b64decode(task.envs['DB_CONFIG']))
    new_dsn = db_config[0]['db']['dsn'].replace('localhost', nodes[0].hostname)
    db_config[0]['db']['dsn'] = new_dsn
    task._envs['DB_CONFIG'] = base64.b64encode(
        json.dumps(
            db_config,
            cls=GuillotinaConfigJSONEncoder,
            ensure_ascii=False
        ).encode('utf-8')).decode('utf-8')
