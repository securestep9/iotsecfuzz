import os
import venv
import json
import sys
from . import pycharm
from pathlib import Path
from ....core import logger
from pkgutil import get_data
from ....util import activate_virtualenv
from ....console.logging import run_with_logger

start_script_template = get_data('isf.resources',
                                 'templates/start.py.tpl').decode()

debug_script_template = get_data('isf.resources',
                                 'templates/debug.py.tpl').decode()

pycharm_script_template = get_data('isf.resources',
                                   'templates/pycharm.py.tpl').decode()

gitignore_template = get_data('isf.resources',
                              'templates/gitignore.tpl').decode()

install_url = 'git+https://gitlab.com/invuls/iot-projects/iotsecfuzz.git@1.0'


def init_git(cwd):
    git_dir = os.path.join(cwd, '.git')
    if os.path.isdir(git_dir):
        logger.info('Git repository already exists, skipping creation')
    else:
        logger.info('Creating git repository')
        run_with_logger(['git', 'init'], prefix='git',
                        error_msg='Unable to create git repository; '
                                  + 'is Git installed and available in PATH?')

    # Inject data into .gitignore
    with open(os.path.join(cwd, '.gitignore'), 'at+',
              encoding='utf-8') as out:
        out.write(gitignore_template)

    logger.info('Adding files')
    run_with_logger(['git', 'add', '.'], prefix='git',
                    error_msg='Unable to add files to Git')


def create_virtualenv(dir):
    venv_path = os.path.join(dir, 'venv')
    bin_path = os.path.join(venv_path, 'bin', 'python')

    if os.name == 'nt':
        bin_path = os.path.join(venv_path, 'Scripts', 'python.exe')

    if os.path.isdir(venv_path):
        logger.info('Using the existing virtual environment for SDK home')
        logger.info('Note that you\'ll have to tweak run configurations ' +
                    'manually if directory layout is non-standard')
        return bin_path

    venv.create(venv_path, with_pip=True)
    return bin_path


def create_files(cwd, module_dir):
    logger.info('Creating directories')

    # Create __init__.py file
    open(os.path.join(module_dir, '__init__.py'), 'a').close()

    # Create requirements.txt file
    with open(os.path.join(cwd, 'requirements.txt'), 'at+',
              encoding='utf-8') as out:
        out.write(install_url + '\n')

    logger.info('Generating run scripts')
    scripts_dir = os.path.join(cwd, 'scripts')
    Path(scripts_dir).mkdir(parents=True, exist_ok=True)

    # Create output directory
    Path(os.path.join(cwd, 'out')).mkdir(parents=True, exist_ok=True)

    start_script_path = os.path.join(scripts_dir, 'start.py')
    with open(start_script_path, 'wt', encoding='utf-8') as out:
        out.write(start_script_template)

    return scripts_dir


def setup_environment(manifest, args):
    cwd = os.getcwd()
    module_dir = os.path.join(cwd, 'isf', *manifest['category'].split('/'),
                              manifest['name'])
    Path(module_dir).mkdir(parents=True, exist_ok=True)
    manifest_path = os.path.join(module_dir, 'manifest.json')
    if os.path.exists(manifest_path):
        logger.error(
            'Init failed: manifest.json already exists in target directory')
        exit(0)

    logger.info('Writing manifest.json file')
    with open(manifest_path, 'wt', encoding='utf-8') as out:
        json.dump(manifest, out, indent=2, sort_keys=False)

    scripts_dir = create_files(cwd, module_dir)

    debug_template = \
        debug_script_template.replace('$PYCHARM_DEBUG_CONFIG$',
                                      pycharm_script_template
                                      if args.pycharm else '')

    debug_script_path = os.path.join(scripts_dir, 'debug.py')
    with open(debug_script_path, 'wt', encoding='utf-8') as out:
        out.write(debug_template)

    if not args.no_venv:
        logger.info('Creating virtual environment')
        bin_path = create_virtualenv(cwd)

        # For Windows
        if os.name == 'nt':
            bin_path = bin_path.replace('\\', '\\\\')

        # Activate virtualenv
        activate_virtualenv(os.path.dirname(bin_path))

    else:
        bin_path = sys.executable

    # Required for find_namespace_packages feature to work
    logger.info('Upgrading setuptools')
    run_with_logger(
        [bin_path, '-m', 'pip', 'install', '--upgrade', 'setuptools'],
        prefix='pip', error_msg='Unable to upgrade setuptools')

    logger.info('Installing requirements')
    run_with_logger(
        [bin_path, '-m', 'pip', 'install', '-r', 'requirements.txt'],
        prefix='pip', error_msg='Unable to install required packages')

    if args.pycharm:
        pycharm.init_pycharm_project(args, cwd, manifest, bin_path)
        pycharm.install_debugger_package(bin_path)

    if not args.no_git:
        init_git(cwd)
