#!/usr/bin/env python

from os import name

from setuptools import setup, find_packages

from teletype import VERSION

with open("readme.md", "r") as fp:
    LONG_DESCRIPTION = fp.read()

setup(
    author="Jessy Williams",
    author_email="jessy@jessywilliams.com",
    description="A high-level cross platform tty library",
    include_package_data=True,
    license="MIT",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    name="teletype",
    packages=find_packages(),
    url="https://github.com/jkwill87/teletype",
    version=VERSION,
)
