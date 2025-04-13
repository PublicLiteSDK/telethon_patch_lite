from setuptools import find_packages, setup
import subprocess
import pkg_resources
import sys

setup(
    name='telethon_patch',
    packages=find_packages(exclude=['tests']),
    version='0.1.0',
    description='Lite Patch for Telethon',
    author='anon',
    license='MIT',
    install_requires=[
        'simple_singleton',
        'telethon',
        'phonenumbers',
        'pytz',
        'aiofile',
        'pydantic',
        'python_socks[asyncio]',
    ],
)
