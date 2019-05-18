from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path


here = path.abspath(path.dirname(__file__))


# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='autoparse',

    version='1.0.0',

    description='Analysis pipeline for cybersecurity',

    long_description=long_description,

    url='',

    author='Mark Moloney',

    author_email='',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Cybersecurity',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6'
    ],

    keywords='cybersecurity NLP',

    packages=find_packages(exclude=['contrib', 'docs', 'tests']),

    install_requires=['elasticsearch', 'elasticsearch-dsl', 'falcon', 'gunicorn', 'iocextract',
                      'Keras', 'matplotlib', 'numpy', 'pandas', 'pytest', 'python-arango',
                      'python-dotenv', 'requests', 'scikit-learn', 'scipy', 'sigmatools', 'spacy',
                      'tensorflow', 'urllib3'],

    entry_points={
        'console_scripts': [
            'read_from_es=read_from_es:main',
            'parse=parse:main',
            'load=load:main'
        ]
    }
)
