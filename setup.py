from setuptools import setup

setup(
    name='chem-spider',
    version='1.0',
    packages=['chem_spider', 'chem_spider.pubchem_spider'],
    url='',
    license='MIT',
    author='Kotori',
    author_email='yzjkid9@gmail.com',
    description='',
    install_requires=[
        "aiohttp>=3.8.1"
    ]
)
