#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import io
import re
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext

from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    return io.open(
        join(dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ).read()


setup(
    name='FPEAM',
    version='2.5.0',
    license='BSD 2-Clause License',
    description='Feedstock Production Emissions to Air Model',
    long_description='%s\n%s' % (
        re.compile('^.. start-badges.*^.. end-badges', re.M | re.S).sub('', read('README.md')),
        re.sub(':[a-z]+:`~?(.*?)`', r'``\1``', read('CHANGELOG.md'))
    ),
    author='Dylan Hettinger, Rebecca Hanes',
    author_email='dylan.hettinger@nrel.gov; rebecca.hanes@nrel.gov',
    url='https://github.com/NREL/fpeam',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    package_data={'FPEAM': ['data/equipment/*.csv',
                            'data/inputs/*.csv',
                            'data/outputs/*.csv',
                            'data/production/*.csv',
                            'configs/*.spec',
                            'configs/*.ini']},
    include_package_data=True,
    python_requires='>=3.5',
    zip_safe=True,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Free To Use But Restricted',
        'Natural Language :: English',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Scientific/Engineering',
    ],
    keywords=[
        'biomass',
        'bioenergy',
        'air quality',
        'pollutants',
        'supply chain'
    ],
    install_requires=[
        'pandas',
        'configobj',
        'networkx',
        'pymysql',
        'lxml',
        'joblib',
        'scipy',
        'matplotlib',
        'seaborn',
        'PyQt5',
        'geopandas'
    ],
    entry_points={
        'console_scripts': [
            'fpeam = FPEAM.scripts.fpeam:main',
        ]
    },
)
