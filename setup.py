"""
DATCHK
A command line datfile parser and rom validator written in python.

Written By: Daws
"""

from setuptools import setup

# TODO: This is throwing a UnicodeDecodeError during pip install on Windows machines.
# L_DESC = open('README.md').read()

setup(
    name="datchk",
    version="0.1",
    author="Daws",
    author_email="0xdaws@protonmail.com",
    description="Command line datfile parser and validator",
    url="https://github.com/0xDAWS/datchk",
    packages=["datchk"],
    install_requires=["rich", "py7zr"],
    python_requires=">=3.10",
    long_description_content_type="text/markdown",
    # long_description=L_DESC,
    license="MIT",
    entry_points={"console_scripts": ["datchk=datchk.__main__:main"]},
)
