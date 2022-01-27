import io
import os
import re

from setuptools import setup, find_packages

requirements = [
    "matplotlib",
    "numpy"
    "pandas=1.3.5",
    "requests",
    "urllib3"
]


# Read the version from the __init__.py file without importing it
# def read(*names, **kwargs):
#     with io.open(
#             os.path.join(os.path.dirname(__file__), *names),
#             encoding=kwargs.get("encoding", "utf8")
#     ) as fp:
#         return fp.read()


# def find_version(*file_paths):
#     version_file = read(*file_paths)
#     version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
#                               version_file, re.M)
#     if version_match:
#         return version_match.group(1)
#     raise RuntimeError("Unable to find version string.")


setup(name='novametrics',
    version= '0.2',
    description='A workflow for modeling building energy upgrades and producing relevant metrics.',
    author='Sean Ericson',
    author_email='Sean.Ericson@nrel.gov',
    url='https://github.com/sericson0/nova_metrics',
    packages=find_packages(include=['exampleproject', 'exampleproject.*'])
    install_requires=requirements,
    package_data={'ochre': ['../defaults/*', '../defaults/*/*']},
    )