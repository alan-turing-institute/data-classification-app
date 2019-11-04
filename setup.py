# coding=utf-8
"""
Setup for Haven
"""

from setuptools import setup, find_packages
import versioneer

# Get the long description
with open('README.rst') as f:
    long_description = f.read()

setup(
    name='Data Safe Haven',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description='Data Safe Havens in the cloud',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='https://gitlab.com/alan-turing-institute/data-safe-haven-webapp',
    author='The Alan Turing Institute',
    license='MIT License',
    packages=find_packages(
    ),
)
