# -*- coding: utf-8 -*-
from guillotina import configure
from guillotina.addons import Addon
from guillotina.content import create_content_in_container
from guillotina_hive.interfaces import IHiveFolder
from zope.interface import alsoProvides


async def install_hive(container, request):
    if not await container.async_contains('+tasks'):
        folder = await create_content_in_container(
            container, 'Folder', '+tasks',
            id='+tasks', creators=('root',),
            contributors=('root',))
        alsoProvides(folder, IHiveFolder)


async def uninstall_hive(container, request):
    if await container.async_contains('+tasks'):
        await container.async_del('+tasks')


@configure.addon(
    name='hive',
    title='Hive installation')
class CanonicalAPIAddon(Addon):

    @classmethod
    async def install(cls, container, request):

        # Create default content
        await install_hive(container, request)

    @classmethod
    async def uninstall(cls, container, request):
        await uninstall_hive(container, request)
