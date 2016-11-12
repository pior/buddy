from setuptools import find_packages, setup

dependencies = ['boto3', 'click', 'pyyaml', 'tabulate', 'Arrow']

setup(
    name='buddy',
    version='0.0.0',
    url='',
    description='Buddy, your Cloudformation/ECS valet',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=dependencies,
    entry_points={
        'console_scripts': [
            'bcluster = buddy.command.cluster:cli',
            'bstack = buddy.command.stack:cli',
        ],
    },
)
