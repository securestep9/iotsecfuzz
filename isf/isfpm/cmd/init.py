import os
import json
import getpass
import semver
from pathlib import Path
from ... import core
from ... import module
from ...console.console import logger
from prompt_toolkit import prompt, HTML

prompt_template = '<a fg="#8E33CE">[?]</a> <a fg="#FFFFFF">%s: </a>'

start_script_template = '''
import os
import subprocess

module_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
subprocess.run(['isf', '--module-dir', module_dir])

'''

debug_script_template = '''
import os
import subprocess

module_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
subprocess.run(['isf', '--dev', '--module-dir', module_dir])

'''


def prompt_data(name, default):
    data = prompt(HTML(prompt_template % (
            'Enter module %s (%s)' % (name, default))))
    return data if data else default


def prompt_authors(default):
    author = prompt(HTML(prompt_template % (
            'Enter module author\'s name (%s)' % default)))
    return [author] if author else [default]


def prompt_description():
    desc = prompt(HTML(prompt_template % 'Enter module description'))
    return desc if desc else ''


def prompt_version(default):
    while True:
        version = prompt(
            HTML(prompt_template % ('Enter module version (%s)' % default)))
        if version and semver.parse(version, loose=False) is None:
            logger.warn('Please check your input.')
            logger.warn('Version must be a valid semver.')
        else:
            return version if version else default


def prompt_category(default):
    while True:
        category = prompt(
            HTML(prompt_template % ('Enter module category (%s)' % default)))
        if category and category not in module.CATEGORIES:
            logger.warn('Please check your input.')
            logger.warn('Category should be one of: ')
            print(json.dumps(module.CATEGORIES, indent=4))
        else:
            return category if category else default


def setup_environment(manifest):
    logger.info('Creating directories')
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

    logger.info('Creating directories')

    # Create __init__.py file
    open(os.path.join(module_dir, '__init__.py'), 'a').close()

    # Create requirements.txt file
    open(os.path.join(module_dir, 'requirements.txt'), 'a').close()

    logger.info('Generating run scripts')
    scripts_dir = os.path.join(cwd, 'scripts')
    Path(scripts_dir).mkdir(parents=True, exist_ok=True)

    start_script_path = os.path.join(scripts_dir, 'start.py')
    with open(start_script_path, 'wt', encoding='utf-8') as out:
        out.write(start_script_template)

    debug_script_path = os.path.join(scripts_dir, 'debug.py')
    with open(debug_script_path, 'wt', encoding='utf-8') as out:
        out.write(debug_script_template)


def run():
    try:
        logger.info('This utility will walk you through creating ' +
                    'environment for your ISF module.')
        logger.info('It will set up the necessary ' +
                    'file structure and the manifest.json file.')
        manifest = {
            'manifest-version': 1,
            'name': prompt_data('name', os.path.basename(os.getcwd())),
            'version': prompt_version('1.0.0'),
            'category': prompt_category('hardware'),
            'description': prompt_description(),
            'authors': prompt_authors(getpass.getuser()),
            'license': prompt_data('license', 'MIT'),
            'input': {},
            'dependencies': {}
        }

        logger.info('Resulting manifest.json file:')
        print(json.dumps(manifest, indent=2, sort_keys=False))
        ok = prompt(HTML(prompt_template % 'Is this OK? (Yes)'))
        if ok and ok.lower() not in ('y', 'yes', 'true'):
            logger.warn('Init aborted')
            exit(0)
        setup_environment(manifest)
        logger.info('Environment setup finished successfully!')
    except KeyboardInterrupt:
        logger.warn('Init cancelled')
    except Exception as e:
        logger.error('Init failed: ', exc_info=e)
