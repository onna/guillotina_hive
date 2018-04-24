from guillotina.commands import Command
from guillotina.component import get_utility
from guillotina.interfaces import IApplication
from guillotina.interfaces import IContainer
from guillotina.interfaces import IDatabase
from guillotina.utils import navigate_to
from guillotina_hive.content.execution import IExecution
from guillotina_hive.exceptions import NoTaskFunctionDefinedError
from guillotina_hive.model.task import Task as TaskObject

import aiotask_context
import json
import logging
import os


logger = logging.getLogger('guillotina_hive')


class WorkerCommand(Command):
    description = 'Guillotina hive worker worker'

    def get_parser(self):
        parser = super(WorkerCommand, self).get_parser()
        parser.add_argument(
            '--task_id',
            help='Task absolute path to get info',
            default=None)
        parser.add_argument(
            '--tags',
            help='Define tags to run this server on',
            default=None)
        parser.add_argument(
            '--payload',
            help='JSON Payload of the task (prefered usage is as an ENV VAR)',
            default=None)
        return parser

    async def run(self, arguments, settings, app):
        aiotask_context.set('request', self.request)
        if arguments.task_id is not None:
            task = arguments.task_id
            payload_config = False
        else:
            if hasattr(arguments, 'payload') and arguments.payload is not None:
                task = arguments.payload
                task = json.loads(task)
            else:
                task = os.environ.get('PAYLOAD', '{}')
                logger.warning(f"Task to do: \n {task}")
                task = json.loads(task)
            payload_config = True
        tags = []
        if arguments.tags:
            tags = json.loads(arguments.tags)

        logger.warning("Tasks available: \n")
        for k, v in settings.get('hive_tasks', {}).items():
            logger.warning(f"{k}: {v}")
        task_obj = None
        root_obj = get_utility(IApplication, name='root')
        if payload_config is False:
            elements = task.split('/')[1:]
            db_obj = await root_obj.async_get(elements[0])
            if IDatabase.providedBy(db_obj):
                tm = self.request._tm = db_obj.get_transaction_manager()
                tm.request = self.request
                self.request._db_id = elements[0]
                self.request._txn = txn = await tm.begin(self.request)
                container_obj = await db_obj.async_get(elements[1])
                if IContainer.providedBy(container_obj):
                    guillotina_execution = await navigate_to(
                        container_obj, '/'.join(elements[2:]))
                    if IExecution.providedBy(guillotina_execution):
                        task_obj = TaskObject(
                            data=guillotina_execution.get_task_payload())
                await tm.abort(txn=txn)
        elif payload_config is True:
            task_obj = TaskObject(data=task)

        if task_obj is None:
            raise NoTaskFunctionDefinedError()
        logger.warning("Ready to run")
        return await task_obj.run(self.request, tags, root_obj)
