import logging

from guillotina import app_settings
from guillotina import configure
from guillotina.content import Item
from guillotina.interfaces import IAbsoluteURL
from guillotina_hive.interfaces import IExecution

logger = logging.getLogger('guillotina_hive')


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
