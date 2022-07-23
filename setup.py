from setuptools import setup

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
name='datchk',
version='0.1',
author='0xDaws',
author_email='0xdaws@protonmail.com',
description='Command line datfile parser and validator',
packages=['datchk'],
install_requires=['rich', 'py7zr'],
)
