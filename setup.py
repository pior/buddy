from setuptools import find_packages, setup

dependencies = ['boto3', 'click', 'pyyaml', 'tabulate', 'Arrow']

classifiers = [
    'Development Status :: 3 - Alpha',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Natural Language :: English',
    'Operating System :: POSIX :: Linux',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: Implementation :: CPython',
    'Topic :: System',
    'Topic :: Software Development',
]

entry_points = {
    'console_scripts': [
        'bcluster = buddy.command.cluster:cli',
        'bstack = buddy.command.stack:cli',
    ],
}


setup(
    name='buddy',
    version='0.0.1',

    description='Buddy, your Cloudformation/ECS valet',
    license='MIT License',
    platforms='Linux',
    classifiers=classifiers,

    url='https://github.com/pior/buddy',
    author='Pior Bastida',
    author_email='pior@pbastida.net',

    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=dependencies,
    entry_points=entry_points,
)
