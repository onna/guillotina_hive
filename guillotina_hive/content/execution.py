from guillotina import app_settings
from guillotina import configure
from guillotina.content import Item
from guillotina.interfaces import IAbsoluteURL
from guillotina.utils import get_dotted_name
from guillotina_hive.interfaces import IExecution

import logging


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
        function = app_settings['hive_tasks'][name]
        if isinstance(function, dict) and 'klass' in function:
            function = get_dotted_name(function['klass'])
        return {
            'name': name,
            'task_uri': IAbsoluteURL(self)(relative=True),
            'function': function,
            'args': self.params,
            'persistent': True
        }
