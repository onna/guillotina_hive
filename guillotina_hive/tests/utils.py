import base64
import json

from guillotina.tests.utils import ContainerRequesterAsyncContextManager
from guillotina_hive.utils import GuillotinaConfigJSONEncoder


class HiveRequesterAsyncContextManager(ContainerRequesterAsyncContextManager):

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
