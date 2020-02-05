from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name='poreTally',
    version='0.1',
    packages=['poreTally'],
    install_requires=['six', 'gitpython', 'snakemake', 'pyYAML', 'mappy', 'biopython', 'ete3', 'tabulate',
                      'psutil', 'requests', 'NanoPlot', 'pexpect', 'quast==4.6.3'],
    author='Carlos de Lannoy',
    author_email='carlos.delannoy@wur.nl',
    description='Benchmark nanopore read assembly tools and publish results in a heartbeat',
    long_description=readme(),
    license='GPL-3.0',
    keywords='nanopore sequencing pipeline benchmark MinION ONT',
    url='https://github.com/cvdelannoy/poreTally',
    entry_points={
        'console_scripts': [
            'poreTally = poreTally.__main__:main'
        ]
    },
    include_package_data=True
)
