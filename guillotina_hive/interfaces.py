import json

from guillotina.async_util import IAsyncUtility
from guillotina.directives import write_permission
from guillotina.interfaces import IFolder
from guillotina.interfaces import IItem
from guillotina.interfaces import Interface
from guillotina.schema import Int
from guillotina.schema import JSONField
from guillotina.schema import TextLine


GENERIC_SCHEMA = json.dumps({
    'type': 'object',
    'properties': {}
})


PARAMS_SCHEMA = json.dumps({
    'type': 'object',
    'properties': {}
})


class IHiveClientUtility(IAsyncUtility):
    """Async utility for hive"""


class IHiveWorkerUtility(IAsyncUtility):
    """Async utility for hive"""


class IHiveFolder(Interface):
    """Marker interface for IHiveFolder"""


class IDequeFolder(IFolder):
    write_permission(username='hive.Manage')
    max_len = Int(
        title='Maximum length of the folder',
        default=0)


class ITask(IDequeFolder):

    caller = TextLine(
        title='Function to call'
    )

    image = TextLine(
        title='Image to call'
    )

    args = JSONField(
        title='Arguments',
        schema=GENERIC_SCHEMA
    )


class IDistTask(ITask):

    workers = Int(title="Num workers")

    masters = Int(title="Num masters")

    ps = Int(title="Num ps")


class IExecution(IItem):

    status = TextLine(title='Status information or error')

    params = JSONField(
        title='Params information about the execution',
        schema=PARAMS_SCHEMA)
