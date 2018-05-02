from guillotina.component import get_utility
from guillotina.interfaces import ICatalogUtility
from guillotina.tests.utils import ContainerRequesterAsyncContextManager
from guillotina_hive.utils import GuillotinaConfigJSONEncoder

import asyncio
import base64
import json
import os


IS_TRAVIS = 'TRAVIS' in os.environ


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
        except Exception:  # noqa
            pass
        _, status = await self.requester(
            'POST',
            '/db/guillotina/@addons',
            data=json.dumps({
                'id': 'hive'
            })
        )
        assert status == 200
        return self.requester

    async def __aexit__(self, exc_type, exc, tb):
        for task in asyncio.Task.all_tasks():
            task._log_destroy_pending = False
        return await super().__aexit__(exc_type, exc, tb)


async def reconfigure_db(hive, task):
    nodes = await hive.cm.get_nodes()
    settings = base64.b64decode(task.envs['APP_SETTINGS'])
    db_config = json.loads(settings)['databases']
    if not IS_TRAVIS:
        new_dsn = db_config['db']['dsn'].replace('localhost', nodes[0].hostname)
    else:
        myip = os.environ['MYIP']
        # import socket
        # myip = socket.gethostbyname(nodes[0].hostname)
        new_dsn = db_config['db']['dsn'].replace('localhost', myip)
    # else:
    #     new_dsn = db_config['db']['dsn'].replace('localhost', '10.0.2.2')
    db_config['db']['dsn'] = new_dsn
    task._envs['APP_SETTINGS'] = base64.b64encode(
        json.dumps(
            {
                "databases": db_config
            },
            cls=GuillotinaConfigJSONEncoder,
            ensure_ascii=False
        ).encode('utf-8')).decode('utf-8')
