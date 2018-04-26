from guillotina.auth.participation import GuillotinaParticipation
from guillotina.auth.users import GuillotinaUser
from guillotina.browser import get_physical_path
from guillotina.component import getUtility
from guillotina.interfaces import ICatalogUtility
from guillotina.interfaces import IFolder
from guillotina.security.policy import Interaction
from guillotina.transactions import get_tm
from guillotina.transactions import get_transaction
from guillotina.traversal import traverse
from guillotina.utils import apply_coroutine
from guillotina.utils import resolve_dotted_name
from guillotina_hive.decorators import hive_task
from urllib.parse import urlparse

import yarl


try:
    from guillotina_elasticsearch.migration import Migrator
    from guillotina_elasticsearch.reindex import Reindexer
except ImportError:
    Migrator = None
    Reindexer = None


@hive_task(name='es-reindex')
async def es_reindex(path, root, request, reindex_security=False):
    try:
        ob, end_path = await traverse(request, root, path.lstrip('/').split('/'))
        assert len(end_path) == 0
        search = getUtility(ICatalogUtility)
        full = True
        if reindex_security:
            full = False
        reindexer = Reindexer(
            search, ob,
            reindex_security=reindex_security,
            full=full,
            request=request,
            log_details=True)
        await reindexer.reindex(ob)
    finally:
        txn = get_transaction(request)
        if txn is not None:
            tm = get_tm(request)
            await tm.abort(txn=txn)


@hive_task(name='es-migrate')
async def es_migrate(path, root, request, reindex_security=False,
                     mapping_only=False, full=False, force=False):
    try:
        ob, end_path = await traverse(
            request, root, path.lstrip('/').split('/'))
        if len(end_path) != 0:
            raise Exception('Could not found object')
        search = getUtility(ICatalogUtility)
        migrator = Migrator(
            search, ob,
            reindex_security=reindex_security,
            full=full,
            force=force,
            mapping_only=mapping_only,
            request=request,
            log_details=True)
        await migrator.run_migration()
    finally:
        txn = get_transaction(request)
        if txn is not None:
            tm = get_tm(request)
            await tm.abort(txn=txn)


async def _apply_recursive(ob, function, count=0):
    await apply_coroutine(function, ob)
    if IFolder.providedBy(ob):
        keys = await ob.async_keys()
        for key in keys:
            item = await ob._p_jar.get_child(ob, key)
            if item is not None:
                count += await _apply_recursive(item, function)
    return count + 1


def login_user(request, user_data):
    request.security = Interaction(request)
    participation = GuillotinaParticipation(request)
    participation.interaction = None

    if 'id' in user_data:
        user = GuillotinaUser(request)
        user.id = user_data['id']
        user._groups = user_data.get('groups', [])
        user._roles = user_data.get('roles', [])
        user.data = user_data.get('data', {})
        participation.principal = user
        request._cache_user = user

    request.security.add(participation)
    request.security.invalidate_cache()
    request._cache_groups = {}
    if user_data.get('Authorization'):
        request.headers['Authorization'] = user_data['Authorization']


def setup_request(request, user_data):
    if 'container_url' in user_data and getattr(request, '_db_id', None):
        container_url = user_data['container_url']
        parsed_url = urlparse(container_url)
        request._cache.clear()
        if 'https' in container_url:
            request._secure_proxy_ssl_header = ('FORCE_SSL', 'true')
            request.headers['FORCE_SSL'] = 'true'
        request.headers.update({
            'HOST': parsed_url.hostname,
            'X-VirtualHost-Monster': container_url.replace(
                request._db_id + '/'.join(get_physical_path(request.container)), ''
            )
        })
        request._rel_url = yarl.URL(yarl.URL(container_url).path)


@hive_task(name='apply-recursive')
async def apply_recursive(path, user_data, root, request, function,
                          commit=False, args=None, kwargs=None):
    '''
    Required options in task data are:
        - path: base path to start using apply on
        - function: what function to apply ob on
        - commit: should we commit after finishing, defaults to false
        - user_data: {id, roles, groups}
        - args: []
        - kwargs: {}
    '''
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    try:
        login_user(request, user_data)
        ob, end_path = await traverse(request, root, path.lstrip('/').split('/'))
        assert len(end_path) == 0
        setup_request(request, user_data)
        function = resolve_dotted_name(function)
        result = await _apply_recursive(
            ob, function,
            *args,
            **kwargs)
    finally:
        txn = get_transaction(request)
        if txn is not None:
            tm = get_tm(request)
            if commit:
                await tm.commit(txn=txn)
            else:
                await tm.abort(txn=txn)
    return result


@hive_task(name='apply-object')
async def apply_object(path, user_data, root, request, function,
                       commit=False, args=None, kwargs=None):
    '''
    Required options in task data are:
        - path: base path to start using apply on
        - function: what function to apply ob on
        - commit: should we commit after finishing, defaults to false
        - user_data: {id, roles, groups}
        - args: []
        - kwargs: {}
    '''
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    path = path
    try:
        login_user(request, user_data)
        ob, end_path = await traverse(request, root, path.lstrip('/').split('/'))
        assert len(end_path) == 0
        setup_request(request, user_data)
        function = resolve_dotted_name(function)
        return await apply_coroutine(
            function, ob,
            *args,
            **kwargs)
    finally:
        txn = get_transaction(request)
        if txn is not None:
            tm = get_tm(request)
            if commit:
                await tm.commit(txn=txn)
            else:
                await tm.abort(txn=txn)
