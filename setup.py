# Copyright © 2022 Alexander L. Hayes
# MIT License

from setuptools import setup
from setuptools import find_packages

from codecs import open
from os import path

# Get __version__ from _version.py
with open(path.join("roofworld", "_version.py")) as _fh:
    exec(_fh.read())

_here = path.abspath(path.dirname(__file__))
with open(path.join(_here, "README.md"), "r", encoding="utf-8") as _fh:
    LONG_DESCRIPTION = _fh.read()

setup(
    name="roofworld",
    packages=find_packages(exclude=["tests"]),
    package_dir={"roofworld": "roofworld"},
    author="Alexander L. Hayes",
    author_email="alexander@batflyer.net",
    description="",
    version=__version__,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    license="MIT License",
    python_requires=">=3.7",
    install_requires=["numpy", "srlearn==0.5.5", "relational-datasets>=0.2.2"],
    extra_requires={
        "tests": ["coverage", "pytest"],
    },
)
