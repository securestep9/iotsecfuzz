import os
import json
import getpass
import semver
from ... import core
from ... import module
from ...console.console import logger
from prompt_toolkit import prompt, HTML

prompt_template = '<a fg="#8E33CE">[?]</a> <a fg="#FFFFFF">%s: </a>'


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


def run():
    try:
        logger.info('This utility will walk you through creating ' +
                    'environment for your ISF module.')
        logger.info('It will set up the necessary ' +
                    'file structure and the manifest.json file.')
        cwd = os.getcwd()
        manifest = {
            'manifest-version': 1,
            'name': prompt_data('name', os.path.basename(cwd)),
            'version': prompt_version('1.0.0'),
            'category': prompt_category('hardware'),
            'description': prompt_description(),
            'authors': prompt_authors(getpass.getuser()),
            'license': prompt_data('license', 'MIT'),
            'input': {},
            'dependencies': {}
        }
        logger.info('Resulting manifest.json file:')
        print(json.dumps(manifest, indent=4, sort_keys=False))
        ok = prompt(HTML(prompt_template % 'Is this OK? (Yes)'))
        if ok and ok.tolower() not in ('y', 'yes', 'true'):
            logger.warn('Init aborted')
            exit(0)

        # TODO finish init

    except KeyboardInterrupt:
        logger.warn('Init cancelled')
    except Exception as e:
        logger.error('Init failed: ', exc_info=e)
