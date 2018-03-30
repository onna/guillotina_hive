import logging

from guillotina.content import Folder
from guillotina.directives import write_permission
from guillotina.interfaces import IFolder
from guillotina.interfaces import IResource
from guillotina.schema import Int
from guillotina.utils import get_current_request

GET_OLDEST_CHILDREN = """
    SELECT id
    FROM objects
    WHERE parent_id = $1::varchar(32)
    ORDER BY tid
    LIMIT 1
    OFFSET 0"""


logger = logging.getLogger('guillotina_hive')


class IDequeFolder(IFolder):
    write_permission(username='hive.Manage')
    max_len = Int(
        title='Maximum length of the folder',
        default=0)


class DequeFolder(Folder):

    async def async_get_oldest(self):
        request = get_current_request()
        txn = request._txn
        conn = txn._db_conn
        smt = await conn.prepare(GET_OLDEST_CHILDREN)
        result = await smt.fetch(self._p_oid)
        if result is None or len(result) == 0:
            return None

        return await txn.get_child(self, result[0]['id'])

    async def async_set(self, key: str, value: IResource) -> None:
        """
        Asynchronously set an object in this folder
        """
        length = await self.async_len()
        if length > self.max_len:
            obj_to_delete = await self.async_get_oldest()
            if obj_to_delete is not None:
                self._get_transaction().delete(obj_to_delete)
        await super(DequeFolder, self).async_set(key, value)