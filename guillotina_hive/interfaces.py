from guillotina.async_util import IAsyncUtility
from guillotina.interfaces import Interface


class IHiveClientUtility(IAsyncUtility):
    """Async utility for hive"""


class IHiveWorkerUtility(IAsyncUtility):
    """Async utility for hive"""


class IHiveFolder(Interface):
    """Marker interface for IHiveFolder"""
