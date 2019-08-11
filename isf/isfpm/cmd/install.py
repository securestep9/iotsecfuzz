import os
import sys
import tarfile
from tempfile import TemporaryDirectory
from ... import core
from ...console.logging import run_with_logger
from shutil import ignore_patterns, copytree

description = 'install ISF modules'


class ModuleInstallationError(Exception):
    pass


def add_arguments(parser):
    parser.add_argument('--no-deps', action='store_true',
                        help='skip dependency resolution stage')
    parser.add_argument('module', nargs='+', type=str,
                        help='either module qualified name, path to local '
                             + 'directory or path to local tarball')
    parser.add_argument('--home', type=str, help='framework home directory')


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
        env['PYTHONPATH'] = (';' if os.name == 'nt' else ';').join(sys.path)
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
        tar = tarfile.open(path, 'r:gz')
        tar.extractall(path=tmp_dir)
        tar.close()
        install_from_directory(tmp_dir)


def install_from_url(url):
    raise RuntimeError('Installation from remote origin not supported yet')


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
                 ignore=ignore_patterns('venv', '.git',
                                        '__pycache__', 'out', *to_exclude))
        install_from_directory(copy_path, manifest, manifest_path)


def resolve_home_directory(args):
    cwd = os.getcwd()
    local_home = os.path.join(cwd, '.isf')

    if os.path.isdir(local_home):
        core.HOME_DIR = local_home

    core.init_home_directory(args.home)

    sys.path.extend(core.modules_dirs)


def run(args):
    resolve_home_directory(args)
    for name in args.module:
        if os.path.isdir(name):
            # Try to set up module from directory
            attempt_directory_install(name)
        elif os.path.isfile(name):
            # Try to set up module from tarball
            install_from_tarball(name)
        else:
            # Try to set up module from remote
            install_from_url(name)
