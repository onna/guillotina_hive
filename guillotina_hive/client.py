from aioclustermanager.k8s import K8SContextManager
from aioclustermanager.manager import ClusterManager
from aioclustermanager.nomad import NomadContextManager
from guillotina import app_settings
from guillotina import configure
from guillotina_hive.interfaces import IHiveClientUtility
from guillotina_hive.model.task import Task as TaskObject

import asyncio
import logging


logger = logging.getLogger('guillotina_hive')


@configure.utility(provides=IHiveClientUtility)
class HiveClientUtility:

    def __init__(self):
        self._settings = {}
        self._initialized = False
        self._cluster_manager = None
        self._context_manager = None

    @property
    def initialized(self):
        return self._initialized

    @property
    def cm(self):
        return self._cluster_manager

    @property
    def default_namespace(self):
        return self._default_namespace

    @property
    def default_image(self):
        return self._default_image

    async def initialize(self, app=None, config=None, image=''):
        if config is None:
            config = {}
        self._app = app

        if app.loop is None:
            self._loop = asyncio.get_event_loop()
        else:
            self._loop = app.loop
        self._settings = app_settings['hive']
        self._master = self._settings.get('master', False)
        self._default_image = self._settings.get('default_image', image)

        self._default_namespace = self._settings.get('default_namespace', 'hive')
        self._orchestrator = self._settings.get('orchestrator', 'k8s')
        self._cluster_environment = self._settings.get(
            'cluster_config', config)
        self._quota = self._settings.get('quota', None)
        try:
            if len(self._cluster_environment.keys()) > 0:
                await self.config()
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.warning('Error initializing cluster', exc_info=True)
        finally:
            self._initialized = True

    async def config(self):
        # we need cluster context manager
        if self._orchestrator == 'k8s':
            self._context_manager = K8SContextManager(
                self._cluster_environment, loop=self._loop)
            self._cluster_manager = ClusterManager(
                await self._context_manager.open())

        elif self._orchestrator == 'nomad':
            self._context_manager = NomadContextManager(
                self._cluster_environment, loop=self._loop)
            self._cluster_manager = ClusterManager(
                await self._context_manager.open())

        await self.cm.create_namespace(self.default_namespace)

        if self._quota:
            await self.set_quota(
                self.default_namespace, self._quota['memory'],
                self._quota['cpu'])

    async def set_quota(self, ns, memory, cpu):
        memory = "%dM" % memory
        cpu = "%dm" % cpu
        await self.cm.define_quota(ns, cpu_limit=cpu, mem_limit=memory)

    async def finalize(self):
        if self._initialized:
            await self._context_manager.close()
        self._initialized = False

    def get_task_ns(self, task=None, ns=None):
        if task:
            ns = task.namespace
        if not ns:
            ns = self.default_namespace
        return ns

    def get_task_image(self, task):
        if not task.image:
            return self.default_image
        return task.image

    async def run_task(self, task: TaskObject):
        await self.cm.create_job(
            self.get_task_ns(task),  # namespace
            task.id,  # jobid
            self.get_task_image(task),  # image
            command=task.command,
            args=task.container_args,
            mem_limit=task.mem_limit,
            cpu_limit=task.cpu_limit,
            envvars=task.envs,
            volumes=task.volumes,
            volumeMounts=task.volumeMounts,
            envFrom=task.envFrom,
            entrypoint=task.entrypoint
        )

    async def get_task_status(self, task_name, namespace=None):
        return await self.cm.get_job(self.get_task_ns(None, namespace), task_name)

    async def get_task_log(self, task_name, namespace=None):
        executions = await self.cm.list_job_executions(
            self.get_task_ns(None, namespace), task_name)
        assert len(executions) > 0

        log = await  self.cm.get_execution_log(
            self.get_task_ns(None, namespace), task_name, executions[0].internal_id)
        return log

    async def get_task_executions(self, task_name, namespace=None):
        return await self.cm.list_job_executions(
            self.get_task_ns(None, namespace), task_name)
