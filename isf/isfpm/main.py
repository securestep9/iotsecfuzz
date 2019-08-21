import os
import sys
from .. import core
from ..config import Configuration

config = None

config_default = {
    'repository': 'http://188.166.134.197/',
    'strategy': 'keep_none',
}

config_schema = {
    'type': dict,
    'template': {
        'repository': {
            'type': str,
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

API_URLS = {
    'packages': '/api/v1/packages/all/',
    'publish': '/api/v1/packages/publish/',
    'auth': '/api/v1/auth/',
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
