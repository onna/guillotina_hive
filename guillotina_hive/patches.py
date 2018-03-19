import logging

from guillotina.component import get_utility
from guillotina.utils import get_current_request
try:
    from guillotina_elasticsearch.utility import ElasticSearchUtility  # noqa
    from guillotina_elasticsearch.utility import noop_response
except ImportError:
    noop_response = None
from guillotina_hive.interfaces import IHiveClientUtility
from guillotina_hive.utils import get_full_content_path


logger = logging.getLogger('guillotina_hive')


async def reindex_all_content(self, obj, security=False, response=noop_response):  # noqa
    '''
    Override guillotina_elasticsearch redinex all content method to make it
    use the hive
    '''
    req = get_current_request()
    full_path = get_full_content_path(req, obj)
    hive = get_utility(IHiveClientUtility)
    args = {
        'path': full_path,
    }
    job_id = 'es-reindex'

    task = await hive.get_task_object(req, job_id)

    await hive.run_task(
        req._container_id,
        task,
        args=args,
        cancel_running=True
    )

if noop_response is not None:
    ElasticSearchUtility.reindex_all_content = reindex_all_content
