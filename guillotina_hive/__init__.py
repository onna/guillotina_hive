from guillotina import configure


app_settings = {
    "commands": {
        "hive-worker": "guillotina_hive.commands.worker.WorkerCommand"
    },
    "hive_tasks": {
    },
    "hive": {
        "image": None,
        "default_namespace": "hive",
        "orchestrator": "k8s",
        "cluster_config": {},
        "guillotina_default": {
            "entrypoint": None,
            "volumes": None,
            "volumeMounts": None,
            "envFrom": None,
            "container_args": ["guillotina", "hive-worker"]
        },
        'quota': None,
        'settings_serializer': 'guillotina_hive.utils.settings_serializer'
    }
}


configure.permission('guillotina_hive.Manage', 'Manage hive')
configure.grant(
    permission="guillotina_hive.Manage",
    role="guillotina.Manager")


def includeme(root):
    configure.scan('guillotina_hive.content')
    configure.scan('guillotina_hive.client')
    configure.scan('guillotina_hive.install')
    configure.scan('guillotina_hive.permissions')
    configure.scan('guillotina_hive.api')
    configure.scan('guillotina_hive.builtins')
