from guillotina import configure
from guillotina_hive import patches  # noqa
from guillotina_hive import content  # noqa


app_settings = {
    "commands": {
        "hive-worker": "guillotina_hive.commands.worker.WorkerCommand"
    },
    "hive_tasks": {
    },
    "hive": {
        "default_max_workers": 2,
        "namespace": "hive",
        "orchestrator": "k8s",
        "guillotina_default": {
            "entrypoint": None,
            "volumes": None,
            "volumeMounts": None,
            "envFrom": None
        }
    }
}


configure.permission('guillotina_hive.Manage', 'Manage hive')
configure.grant(
    permission="guillotina_hive.Manage",
    role="guillotina.Manager")


def includeme(root):
    configure.scan('guillotina_hive.client')
    configure.scan('guillotina_hive.install')
    configure.scan('guillotina_hive.permissions')
    configure.scan('guillotina_hive.api')
    configure.scan('guillotina_hive.builtins')
