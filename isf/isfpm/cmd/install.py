import os
import sys
import tarfile
import requests
from tempfile import TemporaryDirectory
from ..remote import RemotePackageRepository
from ..resolver import PackageState, PackageDependency, PackageRepository, \
    PackageResolver
from ..main import resolve_home_directory, get_config, exclude_patterns
from ... import core
from ...console.logging import run_with_logger
from shutil import ignore_patterns, copytree

description = 'install ISF modules'
config = None
repo = None


class ModuleInstallationError(Exception):
    pass


def add_arguments(parser):
    parser.add_argument('--no-deps', action='store_true',
                        help='skip dependency resolution stage')
    parser.add_argument('module', nargs='+', type=str,
                        help='either module qualified name, path to local '
                             + 'directory or path to local tarball')
    parser.add_argument('--home', type=str, help='framework home directory')


def resolve_dependencies(module_name, collected_modules):
    global config, repo
    installed_modules = {}
    for name in collected_modules:
        manifest = collected_modules[name][0]
        dependencies = manifest['dependencies']
        state = PackageState(name, manifest['version'])
        for dependency in dependencies:
            state.dependencies[dependency] = \
                PackageDependency(dependency, dependencies[dependency])
        installed_modules[name] = state

    repo = RemotePackageRepository(config)
    resolver = PackageResolver({module_name: '*'}, repo)
    resolved = resolver.resolve()
    result = {}
    for package in resolved:
        if package in installed_modules \
                and installed_modules[package].version == resolved[package]:
            core.logger.info('Package %s already installed, skipping' % (
                    package + '@' + resolved[package]))
            continue
        # TODO handle version mismatch of already installed package
        result[package + '@' + resolved[package]] = \
            repo.packages[package]['versions'][resolved[package]]
    return result


def install_from_directory(path, manifest=None, manifest_path=None):
    core.logger.info('Installing from ' + path)

    cwd = os.getcwd()
    os.chdir(path)
    try:
        if manifest_path is None or manifest is None:
            collected = core.collect_module_from_directory(path)
            if len(collected) == 0:
                raise ModuleInstallationError('No modules found in ' + path)
            qualified_name = list(collected)[0]
            manifest, manifest_path = collected[qualified_name]

        if not os.path.isfile(manifest_path):
            raise RuntimeError('Missing setup.py file')

        env = os.environ.copy()
        env['PYTHONPATH'] = (';' if os.name == 'nt' else ':').join(sys.path)
        run_with_logger(
            ['python3', 'setup.py', 'install', '--install-lib',
             core.MODULES_DIR],
            prefix='pip', error_msg='Unable to install module', env=env)

        if os.path.isfile('requirements.txt'):
            core.logger.info('Installing python dependencies')
            run_with_logger(
                ['python3', '-m', 'pip', 'install', '-r', 'requirements.txt'],
                prefix='pip', error_msg='Unable to install module', env=env)

        core.logger.info('Successfully installed module %s/%s' % (
            manifest['category'], manifest['name']))
    except Exception as e:
        core.logger.error('Unable to install module', exc_info=e)
    finally:
        os.chdir(cwd)


def install_from_tarball(tarball):
    path = os.path.abspath(tarball)
    with TemporaryDirectory() as tmp_dir:
        core.logger.info('Unpacking to ' + tmp_dir)
        with tarfile.open(path, 'r:' + repo.config['compression']) as tar:
            tar.extractall(path=tmp_dir)
        install_from_directory(tmp_dir)


def download_tarball(url, file_name):
    with open(file_name, 'wb') as f:
        core.logger.info('Downloading %s' % url)
        response = requests.get(url, stream=True)
        total_length = response.headers.get('content-length')
        if total_length is None:
            f.write(response.content)
        else:
            for data in response.iter_content(chunk_size=1024):
                f.write(data)
    core.logger.info('Download complete')


def install_from_repository(name):
    collected_modules = {}
    global config, repo
    for modules_dir in core.modules_dirs:
        collected_modules.update(
            core.collect_module_from_directory(modules_dir))
    if name in collected_modules:
        core.logger.info('Module %s@%s already installed' % (
            name, collected_modules[name][0]['version']))
        exit(0)
    core.logger.info('Resolving dependencies for %s' % name)
    to_install = resolve_dependencies(name, collected_modules)
    core.logger.info('The following modules will be installed:')
    for package in to_install:
        core.logger.info('  - ' + package)
    for package in to_install:
        core.logger.info('Installing package %s' % package)
        url = repo.repo_url + to_install[package]['dist']['tarball']

        # TODO add checksum verification
        integrity = to_install[package]['dist']['tarball']
        with TemporaryDirectory() as tmp_dir:
            tarball_path = os.path.join(tmp_dir, 'release.tar.' + repo.config[
                'compression'])
            download_tarball(url, tarball_path)
            install_from_tarball(tarball_path)
    core.logger.info('Successfully installed %d package(s)' % len(to_install))


def attempt_directory_install(name):
    path = os.path.abspath(name)
    collected = core.collect_module_from_directory(path)
    if len(collected) == 0:
        raise ModuleInstallationError('No modules found in ' + path)

    qualified_name = list(collected)[0]
    manifest, manifest_path = collected[qualified_name]

    to_exclude = []
    if 'exclude' in manifest:
        to_exclude = manifest['exclude']
    with TemporaryDirectory() as tmp_dir:
        copy_path = os.path.join(tmp_dir, 'tree')
        core.logger.info(
            'Copying tree to temporary directory ' + copy_path)
        copytree(path, copy_path,
                 ignore=ignore_patterns(*exclude_patterns, *to_exclude))
        install_from_directory(copy_path, manifest, manifest_path)


def run(args):
    global config
    resolve_home_directory(args.home)
    config = get_config()
    try:
        for name in args.module:
            if os.path.isdir(name):
                # Try to set up module from directory
                attempt_directory_install(name)
            elif os.path.isfile(name):
                # Try to set up module from tarball
                install_from_tarball(name)
            else:
                # Try to set up module from remote
                install_from_repository(name)
    except KeyboardInterrupt:
        core.logger.warn('Installation cancelled by user')
    except Exception as e:
        core.logger.error('unable to install packages:', exc_info=e)
