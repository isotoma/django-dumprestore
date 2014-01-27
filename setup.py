from setuptools import setup, find_packages

version = '0.0.dev0'

setup(
    name='django-dumprestore',
    version=version,
    long_description=open("README.rst").read(),
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'Django',
    ],
    )

