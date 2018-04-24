import logging

from guillotina.content import Folder
from guillotina.interfaces import IResource
from guillotina.transactions import get_transaction

GET_OLDEST_CHILDREN = """
    SELECT id
    FROM objects
    WHERE parent_id = $1::varchar
    ORDER BY tid
    LIMIT 1
    OFFSET 0"""


logger = logging.getLogger('guillotina_hive')


class DequeFolder(Folder):

    async def async_get_oldest(self):
        txn = get_transaction()
        conn = await txn.get_connection()
        result = await conn.fetch(GET_OLDEST_CHILDREN, self._p_oid)
        if result is None or len(result) == 0:
            return None

        return await txn.get_child(self, result[0]['id'])

    async def async_set(self, key: str, value: IResource) -> None:
        """
        Asynchronously set an object in this folder
        """
        length = await self.async_len()
        if length >= self.max_len:
            obj_to_delete = await self.async_get_oldest()
            if obj_to_delete is not None:
                self._get_transaction().delete(obj_to_delete)
        await super(DequeFolder, self).async_set(key, value)
