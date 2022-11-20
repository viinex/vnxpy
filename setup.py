from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='vnxpy',
    version='0.1.4',
    description='An integration module for vnxvideo library of Viinex',
    long_description=readme,
    author='German Zhyvotnikov',
    author_email='gzh@viinex.com',
    url='https://github.com/viinex/vnxpy',
    license=license,
    packages=find_packages(exclude=('examples', 'tests', 'docs'))
)
