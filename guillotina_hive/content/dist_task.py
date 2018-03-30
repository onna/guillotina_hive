from guillotina import configure
from guillotina.schema import Int
from guillotina_hive.content.task import ITask
from guillotina_hive.content.task import Task


class IDistTask(ITask):

    workers = Int(title="Num workers")

    masters = Int(title="Num masters")

    ps = Int(title="Num ps")


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