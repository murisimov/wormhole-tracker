# -*- coding: utf-8 -*-
#
# This file is part of wormhole-tracker package released under
# the GNU GPLv3 license. See the LICENSE file for more information.

from setuptools import setup, find_packages


description = (
    "Third-party web application for EVE online that allows to "
    "track character's location and draws his path in real time"
)

setup(
    name='wormhole-tracker',
    description=description,
    version='0.1a0',
    license='GNU GPLv3',
    author='Andrii Murisimov',
    author_email='murisimov@gmail.com',
    url="https://github.com/murisimov/wormhole-tracker",
    download_url='https://github.com/murisimov/wormhole-tracker',
    classifiers=[
        'Development Status :: 1 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Webmasters',
        'License :: GNU GPLv3',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Programming Languages :: Python, Javascript',
        'Topic :: Internet :: WWW/HTTP',
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=True,
    install_requires=[
        'setuptools',
        'tornado==4.4',
        #'futures>=3.0.5',
    ],
    entry_points={
        'console_scripts': [
            'wormhole-tracker = wormhole_tracker.server:main',
        ]
    },
)
