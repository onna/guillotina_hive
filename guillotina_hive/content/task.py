import json
import logging

from guillotina import configure
from guillotina.interfaces import IObjectAddedEvent
from guillotina.schema import JSONField
from guillotina.schema import TextLine
from guillotina_hive.content.deque_folder import DequeFolder
from guillotina_hive.content.deque_folder import IDequeFolder
from guillotina_hive.decorators import task_registry_info
from guillotina_hive.exceptions import TaskNotFound


logger = logging.getLogger('guillotina_hive')

GENERIC_SCHEMA = json.dumps({
    'type': 'object',
    'properties': {}
})


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


@configure.contenttype(
    type_name='Task',
    schema=ITask,
    behaviors=[
        'guillotina.behaviors.dublincore.IDublinCore'
    ],
    allowed_types=[
        'Execution'
    ])
class Task(DequeFolder):
    pass


@configure.subscriber(for_=(ITask, IObjectAddedEvent))
async def check_id(obj, evnt):

    if task_registry_info(obj.__name__) is None:
        raise TaskNotFound()
