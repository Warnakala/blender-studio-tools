#!/usr/bin/env python

# TODO Put the default_scripts in /usr/share and adjust main Logic to accomodate

"""The setup script."""

from setuptools import setup, find_packages

with open("README.md") as readme_file:
    readme = readme_file.read()


requirements = []

setup_requirements = []

test_requirements = []

setup(
    author="Nick Alberelli",
    author_email="nick@blender.org",
    python_requires=">=3.5",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="Command line tool to perform recursive crawl blend files from the console",
    install_requires=requirements,
    long_description=readme,
    include_package_data=True,
    keywords="blender_crawl",
    name="blender_crawl",
    packages=find_packages(include=["blender_crawl", "blender_crawl.*"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    version="0.1.0",
    zip_safe=False,
    entry_points={"console_scripts": ["blender_crawl = blender_crawl.__main__:main"]},
    data_files=[
        ('default_purge', ['blender_crawl/default_scripts/purge.py'])
        ]
)