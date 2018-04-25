Introduction
============

`guillotina_hive` is a task runner whose main goal is to provide a mechanism
to iterate through all the content on a database as quickly as possible.

To accomplish that end, hive integrates with container orchestrators(k8s or nomad)
to schedule jobs on and retrieve results from those jobs.

Installation
------------

With pip:

    pip install guillotina_hive


Guillotina configuration
------------------------

Example here with json::

    "applications": ["guillotina_hive"],
    "hive": {
        "default_image": None,
        "default_namespace": "hive",
        "orchestrator": "k8s",
        "cluster_config": {},
        "guillotina_default": {
            "entrypoint": None,
            "volumes": None,
            "volumeMounts": None,
            "envFrom": None
        },
        'quota': None
    }


Settings explained
~~~~~~~~~~~~~~~~~~

- default_image: default image to use for jobs to run with
- default_namespace: cluster namespace to use
- orchestrator: k8s or nomad
- cluster_config: what to configure aioclustermanager with
- guillotina_default: default configuration for guillotina jobs
- quota: define quote on cluster namespace


Defining a job
--------------

We use decorators to provide tasks::

    from guillotina_hive.decorators import hive_task
    @hive_task(name='something')
    async def something(arg1, arg2):
        return foobar


You can also use application settings::

    {
        "calculate-numbers": "guillotina_hive.tests.tasks.calculate_numbers"
    }
