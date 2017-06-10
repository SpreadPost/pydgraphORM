# -*- coding: utf-8 -*-
from setuptools import find_packages, setup

setup(
    name='pydgraphORM',
    version='0.1',
    author=u'David Ziegler',
    author_email='webmaster@SpreadPost.de',
    packages=find_packages(),
    include_package_data=True,
    url='https://github.com/SpreadPost/pydgraphORM',
    license='Apache License 2.0',
    description='ORM for dgraph in Python',
    zip_safe=False,
    keywords=['ORM', 'Dgraph'],
    dependency_links=[
        "https://github.com/InfinityMod/pydgraph/tarball/master#egg=pydgraph-0.4.0"
    ],
    install_requires=[
        'pydgraph',
    ],
)