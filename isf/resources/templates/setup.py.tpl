from setuptools import setup, find_namespace_packages

setup(
    name='$NAME$',
    version='$VERSION$',
    description='$DESCRIPTION$',
    author='$AUTHORS$',
    packages=find_namespace_packages(),
    package_data={'$RESOURCES_PACKAGE$': ['*', '**/*']},
    zip_safe=False
)
