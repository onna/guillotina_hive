from guillotina import configure
from guillotina.component import get_utility
from guillotina.interfaces import IApplication
from guillotina_hive.interfaces import IHiveClientUtility


@configure.service(context=IApplication, name='@hive-jobs', method='GET',
                   permission='guillotina_hive.Manage')
@configure.service(context=IApplication, name='@hive-jobs/{job_id}', method='GET',
                   permission='guillotina_hive.Manage')
@configure.service(context=IApplication, name='@hive-jobs/{job_id}/{execution_id}',
                   method='GET', permission='guillotina_hive.Manage')
async def get_jobs(context, request):
    hive = get_utility(IHiveClientUtility)
    if 'job_id' not in request.matchdict:
        jobs = await hive.cm.list_jobs(hive.ns)
        return jobs
    if 'execution_id' not in request.matchdict:
        job_id = request.matchdict['job_id']
        job = await hive.cm.get_job(hive.ns, job_id)
        executions = await hive.cm.list_job_executions(hive.ns, job_id)
        return job, executions
