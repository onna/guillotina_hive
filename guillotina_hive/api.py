from guillotina import configure
from guillotina.api.service import TraversableService
from guillotina.component import get_utility
from guillotina.interfaces import IApplication
from guillotina_hive.interfaces import IHiveClientUtility


class BaseWorkerService(TraversableService):
    job_id = None
    execution_id = None

    async def publish_traverse(self, traverse):
        if len(traverse) > 2:
            raise KeyError('/'.join(traverse))
        if len(traverse) > 0:
            self.job_id = traverse[0]
        if len(traverse) > 1:
            self.execution_id = traverse[1]
        return self


@configure.service(context=IApplication, name='@hive-jobs', method='GET',
                   permission='guillotina_hive.Manage')
class Workers(BaseWorkerService):

    async def __call__(self):

        hive = get_utility(IHiveClientUtility)
        if self.job_id is None:
            jobs = await hive.cm.list_jobs(hive.ns)
            return jobs
        if self.job_id is not None and self.execution_id is None:
            job = await hive.cm.get_job(hive.ns, self.job_id)
            executions = await hive.cm.list_job_executions(hive.ns, self.job_id)
            return job, executions
