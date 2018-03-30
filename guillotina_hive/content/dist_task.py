from guillotina import configure
from guillotina.schema import Int
from guillotina_hive.content.task import ITask
from guillotina_hive.content.task import Task
from guillotina_hive.interfaces import IDistTask



@configure.contenttype(
    type_name='DistTask',
    schema=IDistTask,
    behaviors=[
        'guillotina.behaviors.dublincore.IDublinCore'
    ],
    allowed_types=[
        'Execution'
    ])
class DistTask(Task):
    pass
