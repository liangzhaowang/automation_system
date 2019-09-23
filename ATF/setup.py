from setuptools import setup, find_packages


setup(
    name='ATF',
    version='0.1',
    author='cc',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'requests',
        'redis',
        'pyyaml',
        'pyserial',
    ],
    entry_points={
            'console_scripts': [
                'atf = atf:main',
            ]
    },
    zip_safe=False
)
