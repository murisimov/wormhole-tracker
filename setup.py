# coding: utf-8
from setuptools import setup, find_packages
setup(
    name='wormhole-tracker',
    description='',
    version='0.1a0',
    license='MIT',
    author='Andrii Murisimov',
    author_email='murisimov@gmail.com',
    classifiers=[
        'Development Status :: 2 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Webmasters',
        'Programming Languages :: Python, Javascript',
        'Topic :: Internet :: WWW/HTTP',
    ],
    packages=find_packages(),
    include_package_data = True,
    zip_safe=True,
    install_requires=[
        'setuptools',
        'tornado==4.4',
    ],
    entry_points={
        'console_scripts': [
            'wormhole-tracker = wormhole_tracker.server:main',
        ]
    },
)
