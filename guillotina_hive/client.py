import asyncio
import logging

from aioclustermanager.k8s import K8SContextManager
from aioclustermanager.manager import ClusterManager
from aioclustermanager.nomad import NomadContextManager
import aiohttp
from guillotina import app_settings
from guillotina import configure
from guillotina_hive.interfaces import IHiveClientUtility
from guillotina_hive.model.task import Task as TaskObject


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
    def ns(self):
        return self._cluster_namespace

    @property
    def image(self):
        return self._image

    async def initialize(self, app=None, config={}, image=''):
        self._app = app

        if app.loop is None:
            self._loop = asyncio.get_event_loop()
        else:
            self._loop = app.loop
        self._settings = app_settings['hive']
        self._master = self._settings.get('master', False)
        self._max_workers = self._settings.get('default_max_workers', 2)
        self._image = self._settings.get('image', image)

        self._load_max_workers = self._settings.get('load_max_workers', None)
        self._cluster_namespace = self._settings.get('namespace', 'hive-')
        self._orchestrator = self._settings.get('orchestrator', 'k8s')
        self._cluster_environment = self._settings.get(
            'cluster_config', config)
        if len(self._cluster_environment.keys()) > 0:
            await self.config()

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

        # Assure Namespace
        await self.cm.create_namespace(self.ns)

        if self._master:
            await self.config_max()
        self._initialized = True

    async def finalize(self):
        if self._initialized:
            await self._context_manager.close()
        self._initialized = False

    async def config_max(self):
        max_workers = self._max_workers
        if self._load_max_workers is not None:
            try:
                async with aiohttp.ClientSession() as sess:
                    async with sess.get(self._load_max_workers) as resp:
                        if resp.status == 200:
                            max_workers = int(await resp.text())
            except (aiohttp.errors.ClientResponseError,
                    aiohttp.errors.ClientRequestError,
                    aiohttp.errors.ClientOSError,
                    aiohttp.errors.ClientDisconnectedError,
                    aiohttp.errors.ClientTimeoutError,
                    asyncio.TimeoutError,
                    aiohttp.errors.HttpProcessingError) as exc:
                pass

        memory = max_workers * 2000  # 2000 Mb RAM x CPU
        memory = "%dM" % memory
        cpu = max_workers * 1000
        cpu = "%dm" % cpu
        result = await self.cm.define_quota(
            self.ns,
            cpu_limit=cpu, mem_limit=memory)
        assert result is True
        self._loop.call_later(3660 * 24, self.config_max)

    async def run_task_object(self, task: TaskObject):
        if task.image in ["", None]:
            task._image = self.image

        await self.cm.create_job(
            self.ns,  # namespace
            task.name,  # jobid
            task.image,  # image
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

    async def get_task_status(self, task_name):
        return await self.cm.get_job(self.ns, task_name)

    async def get_task_log(self, task_name):
        executions = await self.cm.list_job_executions(
            self.ns, task_name)
        assert len(executions) > 0

        log = await  self.cm.get_execution_log(
            self.ns, task_name, executions[0].internal_id)
        return log

    async def get_task_executions(self, task_name):
        return await self.cm.list_job_executions(
            self.ns, task_name)

    # async def stream_all_messages(self, request):
    #     # TODO: review
    #     response = StreamResponse()
    #     await response.prepare(request)
    #     futures = []
    #     for worker in self.workers.values():
    #         future = self.get_worker_messages(worker, response)
    #         futures.append(future)
    #     await asyncio.gather(*futures)
    #     return response

    # async def stream_task_messages(self, request, task):
    #     # TODO: review
    #     response = StreamResponse()
    #     await response.prepare(request)
    #     futures = []
    #     for worker in task.workers.values():
    #         future = self.get_worker_messages(worker, response)
    #         futures.append(future)
    #     await asyncio.gather(*futures)
    #     return response
