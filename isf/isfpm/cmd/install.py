import os
import sys
import tarfile
import requests
from tempfile import TemporaryDirectory
from ..main import API_URLS
from ..resolver import PackageState, PackageDependency, PackageRepository, \
    PackageResolver
from ..main import resolve_home_directory, get_config
from ... import core
from ...console.logging import run_with_logger
from shutil import ignore_patterns, copytree

description = 'install ISF modules'


class ModuleInstallationError(Exception):
    pass


class RemotePackageRepository(PackageRepository):

    def __init__(self, repo_url):
        self.repo_url = repo_url
        self.packages = {}

    def query_package(self, name):
        url = f'{self.repo_url}{API_URLS["packages"]}{name}/'
        core.logger.debug('GET ' + url)
        response = requests.get(url)
        data = response.json()
        if response.status_code != 200:
            err = data['detail'] if 'detail' in data else response.reason
            raise ModuleInstallationError(f'Package {name}: {err}')
        self.packages[name] = data

    def get_versions(self, package_name):
        if package_name not in self.packages:
            self.query_package(package_name)
        return list(self.packages[package_name]['versions'].keys())

    def get_dependencies(self, package_name, package_version):
        if package_name not in self.packages:
            self.query_package(package_name)
        if package_version not in self.packages[package_name]['versions']:
            raise ModuleInstallationError('Package %s: no version %s found' % (
                package_name, package_version))
        return self.packages[package_name]['versions'][package_version][
            'manifest']['dependencies']


def add_arguments(parser):
    parser.add_argument('--no-deps', action='store_true',
                        help='skip dependency resolution stage')
    parser.add_argument('module', nargs='+', type=str,
                        help='either module qualified name, path to local '
                             + 'directory or path to local tarball')
    parser.add_argument('--home', type=str, help='framework home directory')


def resolve_dependencies(name, collected_modules):
    installed_modules = {}
    for name in collected_modules:
        manifest = collected_modules[name][0]
        dependencies = manifest['dependencies']
        state = PackageState(name, manifest['version'])
        for dependency in dependencies:
            state.dependencies[dependency] = \
                PackageDependency(dependency, dependencies[dependency])
        installed_modules[name] = state

    config = get_config()
    url = config['repository'].rstrip('/')
    repo = RemotePackageRepository(url)
    resolver = PackageResolver({name: '*'}, repo)
    resolved = resolver.resolve()
    result = {}
    for package in resolved:
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
            ['python', 'setup.py', 'install', '--install-lib',
             core.MODULES_DIR],
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
        with tarfile.open(path, 'r:xz') as tar:
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
        url = to_install[package]['dist']['tarball']

        # TODO add checksum verification
        integrity = to_install[package]['dist']['tarball']
        with TemporaryDirectory() as tmp_dir:
            tarball_path = os.path.join(tmp_dir, 'release.tar.xz')
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
                 ignore=ignore_patterns('venv', '.git', '.idea', '.isf',
                                        '__pycache__', 'out', *to_exclude))
        install_from_directory(copy_path, manifest, manifest_path)


def run(args):
    resolve_home_directory(args.home)
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
