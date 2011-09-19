#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='django-simple-cms',
    version='0.0.2',
    description='Simple CMS for your django powered website',
    author='Charles Mastin',
    author_email='charles@bricksf.com',
    url='https://github.com/charlesmastin/django-simple-cms/',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT',
        'Programming Language :: Python',
    ],
    packages=find_packages(),
    zip_safe=False,
)
