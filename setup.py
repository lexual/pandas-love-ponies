from setuptools import setup


with open('requirements.txt') as f:
    requires = [l.rstrip() for l in f if not l.startswith('#')]
    version = '0.6.0'


setup(
        name='pandas-love-ponies',
        author='Lex Hider',
        description='Write Pandas dataframes to Django models',
        long_description=open('README.md').read(),
        url='https://github.com/lexual/pandas-love-ponies',
        version=version,
        packages=['pandas_love_ponies'],
        license='BSD',
        install_requires=requires
)
