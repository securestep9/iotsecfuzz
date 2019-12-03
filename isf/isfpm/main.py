import os
import sys
from .. import core
from .remote import repo_config_template
from ..config import Configuration

config = None

exclude_patterns = ['venv', '.idea', '.git', '*__pycache__', '__pycache__',
                    'out', '.isf']

root_whitelist = ['isf', 'setup.py', 'requirements.txt', '.gitignore',
                  'README.md', 'readme.md', 'LICENSE.txt', 'license.txt',
                  'LICENSE.md', 'license.md']

config_default = {
    'repository': {
        'url': 'http://188.166.134.197/'
    },
    'strategy': 'keep_none',
}

config_schema = {
    'type': dict,
    'template': {
        'repository': {
            'type': dict,
            'template': {
                'url': {
                    'type': str,
                    'required': True
                },
                'config': {
                    'type': dict,
                    'template': repo_config_template,
                    'required': False
                }
            },
            'required': True,
        },
        'strategy': {
            'type': str,
            'required': True,
            'values': ['keep_all', 'keep_standalone', 'keep_none']
        },
        'auth': {
            'type': dict,
            'template': {
                'username': {
                    'type': str,
                    'required': True
                },
                'token': {
                    'type': str,
                    'required': True
                }
            },
            'required': False
        }
    }
}


def resolve_home_directory(home_arg=None):
    cwd = os.getcwd()
    local_home = os.path.join(cwd, '.isf')

    if os.path.isdir(local_home):
        core.HOME_DIR = local_home

    core.init_home_directory(home_arg)

    sys.path.extend(core.modules_dirs)


def get_config():
    global config
    if config is None:
        config = Configuration(os.path.join(core.DATA_DIR, 'isfpm.json'),
                               schema=config_schema, default=config_default)
        config.load()
    return config
