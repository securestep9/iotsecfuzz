from pathlib import Path
from setuptools import setup, find_namespace_packages


def parse_requirements(filename):
    """Return requirements from requirements file."""
    # Ref: https://stackoverflow.com/a/42033122/
    requirements = (Path(__file__).parent / filename).read_text().strip().split(
        '\n')
    requirements = [r.strip() for r in requirements]
    requirements = [r for r in sorted(requirements) if
                    r and not r.startswith('#') and '+' not in r]
    return requirements


setup(
    install_requires=parse_requirements('requirements.txt'),
    name='$NAME$',
    version='$VERSION$',
    description='$DESCRIPTION$',
    author='$AUTHORS$',
    packages=find_namespace_packages(),
    package_data={'$RESOURCES_PACKAGE$': ['*', '**/*']}
)
