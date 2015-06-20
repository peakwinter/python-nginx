#!/usr/bin/env python

from distutils.core import setup

setup(
    name='python-nginx',
    version='0.1.4',
    description='Create and modify nginx serverblock configs in Python',
    author='Jacob Cook',
    author_email='jacob@peakwinter.net',
    url='https://github.com/peakwinter/python-nginx',
    py_modules=['nginx'],
    keywords = ['nginx', 'web servers', 'serverblock', 'server block'],
    download_url = 'https://github.com/peakwinter/python-nginx/archive/0.1.3.tar.gz',
    license = 'GPLv3',
    classifiers = [
    	"Development Status :: 3 - Alpha",
    	"License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
    	"Operating System :: Unix",
    	"Topic :: Internet :: WWW/HTTP :: HTTP Servers",
    ]
)
