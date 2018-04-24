# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup

setup(
    name='guillotina_hive',
    version=open('VERSION').read().strip(),
    description='Guillotina addon to split actions into smaller bits',  # noqa
    long_description=(open('README.rst').read() + '\n' +
                      open('CHANGELOG.rst').read()),
    keywords=['asyncio', 'REST', 'Framework', 'transactional'],
    author='Ramon Navarro & Nathan VanGheem',
    author_email='ramon@onna.com',
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    url='https://github.com/onna/guillotina_hive',
    license='BSD',
    setup_requires=[
        'pytest-runner',
    ],
    zip_safe=True,
    include_package_data=True,
    packages=find_packages(),
    install_requires=[
        'setuptools',
        'guillotina>=2.1.0',
        'async_timeout',
        'aioclustermanager',
        'psycopg2'
    ],
    extras_require={
        'test': [
            'pytest',
            'docker',
            'backoff',
            'pytest-asyncio',
            'pytest-aiohttp',
            'pytest-cov',
            'pytest-docker-fixtures',
            'guillotina_elasticsearch'
        ]
    }
)
