from pathlib import Path
from setuptools import setup, find_namespace_packages
from setuptools.command.develop import develop
from setuptools.command.install import install


class PostDevelopCommand(develop):
    """Post-installation for development mode."""

    def run(self):
        super().do_egg_install()
        # TODO install standard modules here


class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def run(self):
        super().do_egg_install()
        # TODO install standard modules here


def parse_requirements(filename):
    """Return requirements from requirements file."""
    # Ref: https://stackoverflow.com/a/42033122/
    requirements = (Path(__file__).parent / filename).read_text().strip().split(
        '\n')
    requirements = [r.strip() for r in requirements]
    requirements = [r for r in sorted(requirements) if
                    r and not r.startswith('#')]
    return requirements


setup(
    install_requires=parse_requirements('requirements.txt'),
    name='IoTSecFuzz',
    version='1.0.0',
    description='IoT security testing framework',
    author='Invuls',
    url='https://gitlab.com/invuls/iot-projects/iotsecfuzz',
    packages=find_namespace_packages(),
    package_data={'isf.resources': ['*', '**/*']},
    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
    },
    entry_points={
        'console_scripts': [
            'isf = isf.main:main',
            'isfpm = isf.isfpm.cli:main'
        ],
    }
)
