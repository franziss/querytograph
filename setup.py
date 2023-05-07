# Always prefer setuptools over distutils
from setuptools import setup, find_packages

# To use a consistent encoding
from codecs import open
from os import path

# The directory containing this file
HERE = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(HERE, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='querytograph',
    packages=find_packages(include=['querytograph']),
    version='0.0.1',
    description='Using ChatGPT to convert your plain English queries into graphs',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='franziss',
    author_email='franziss@gmail.com',
    license='MIT',
    install_requires=[
        'pandas',
        'openai',
        'langchain==0.0.160',
        'rapidfuzz==3.0.0',
        'gradio==3.26.0',
        'numpy'
    ],
    setup_requires=[],
    tests_require=[]
)