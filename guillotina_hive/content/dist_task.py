from guillotina import configure
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
