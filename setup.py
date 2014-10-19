# -*- coding: utf-8 -*-

from codecs import open  # To use a consistent encoding
from os import path

from setuptools import find_packages
from setuptools import setup

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='django-rest-params',
    version='1.0.1',

    description='Function decorator for Django REST Framework for specifying and constraining API parameters.',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/cammsaul/django-rest-params',

    # Author details
    author='Cam Saül',
    author_email='cammsaul@gmail.com',

    # Choose your license
    license='BSD',

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
        'Topic :: Internet :: WWW/HTTP',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
    ],

    keywords='rest,django,api,params,parameters,djangorestframework,decorator',

    packages=find_packages(exclude=['tests']),

    install_requires=['django', 'djangorestframework']
)
