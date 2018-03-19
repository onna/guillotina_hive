

from guillotina import configure


configure.permission('hive.Manage', 'Manage Hive Cluster')
configure.permission('hive.Schedulle', 'Schedulle tasks')

configure.grant(
    permission="hive.Manage",
    role="guillotina.ContainerAdmin")
