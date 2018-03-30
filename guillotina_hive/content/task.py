import logging

from guillotina import configure
from guillotina.interfaces import IObjectAddedEvent

from guillotina_hive.content.deque_folder import DequeFolder
from guillotina_hive.decorators import task_registry_info
from guillotina_hive.exceptions import TaskNotFound
from guillotina_hive.interfaces import ITask

logger = logging.getLogger('guillotina_hive')


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
