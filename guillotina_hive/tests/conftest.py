
pytest_plugins = [
    'guillotina.tests.fixtures',
    'aioclustermanager.tests.fixtures',
    'guillotina_hive.tests.fixtures'
]

try:
    import guillotina_elasticsearch  # noqa
    pytest_plugins.append('guillotina_elasticsearch.tests.fixtures')
except ImportError:
    pass
