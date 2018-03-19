import json
import logging

from guillotina import app_settings
from guillotina import configure
from guillotina.content import Item
from guillotina.interfaces import IAbsoluteURL
from guillotina.interfaces import IItem
from guillotina.schema import JSONField
from guillotina.schema import TextLine


logger = logging.getLogger('guillotina_hive')


PARAMS_SCHEMA = json.dumps({
    'type': 'object',
    'properties': {}
})


class IExecution(IItem):

    status = TextLine(title='Status information or error')

    params = JSONField(
        title='Params information about the execution',
        schema=PARAMS_SCHEMA)


@configure.contenttype(
    type_name='Execution',
    schema=IExecution,
    behaviors=[
        'guillotina.behaviors.dublincore.IDublinCore'
    ])
class Execution(Item):

    def get_task_payload(self):
        name = self.__parent__.__name__
        return {
            'name': name,
            'task_uri': IAbsoluteURL(self)(relative=True),
            'function': app_settings['hive_tasks'][name],
            'args': self.params,
            'persistent': True
        }
