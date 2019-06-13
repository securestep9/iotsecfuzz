import os
import json
import getpass
from ....core import logger
from . import prompt
from . import env


description = 'initialize environment for your ISF module'


def add_arguments(parser):
    parser.add_argument('--no-venv', action='store_true',
                        help='skip virtual environment creation and '
                             + 'use current Python interpreter')
    parser.add_argument('--pycharm', action='store_true',
                        help='initialize environment for JetBrains PyCharm')
    parser.add_argument('--no-git', action='store_true',
                        help='skip Git repository creation')


def run(args):
    try:
        logger.info('This utility will walk you through creating ' +
                    'environment for your ISF module.')
        logger.info('It will set up the necessary ' +
                    'file structure and the manifest.json file.')
        manifest = {
            'manifest-version': 1,
            'name': prompt.prompt_data('name', os.path.basename(os.getcwd())),
            'version': prompt.prompt_version('1.0.0'),
            'category': prompt.prompt_category('hardware'),
            'description': prompt.prompt_description(),
            'authors': prompt.prompt_authors(getpass.getuser()),
            'license': prompt.prompt_data('license', 'MIT'),
            'input': {},
            'dependencies': {}
        }

        logger.info('Resulting manifest.json file:')
        print(json.dumps(manifest, indent=2, sort_keys=False))
        ok = prompt.prompt_any('Is this OK? (Yes)')
        if ok and ok.lower() not in ('y', 'yes', 'true'):
            logger.warn('Init aborted')
            exit(0)
        env.setup_environment(manifest, args)
        logger.info('Environment setup finished successfully!')
    except KeyboardInterrupt:
        logger.warn('Init cancelled')
    except Exception as e:
        logger.error('Init failed: ', exc_info=e)
