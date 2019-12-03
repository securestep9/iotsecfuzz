import requests

from .init import prompt
from ..remote import RemotePackageRepository
from ..main import resolve_home_directory, get_config
from ...core import logger

description = 'logs you in to selected ISFPM repository'


def run(args):
    try:
        resolve_home_directory()
        config = get_config()
        logger.info('Logging in to ' + config['repository']['url'])
        username = prompt.prompt_any('Enter username')
        password = prompt.prompt_password('Enter password')
        repo = RemotePackageRepository(config)
        url = repo.repo_url + repo.urls['auth']
        response = requests.post(url, json={'username': username,
                                            'password': password})
        data = response.json()
        if response.status_code != 200:
            if 'non_field_errors' in data:
                err = ';'.join(data['non_field_errors'])
            elif 'detail' in data:
                err = data['detail']
            else:
                err = response.reason
            logger.error('Unable to login: ' + err)
            exit(0)

        if 'token' not in data:
            logger.error('Unable to login: no auth token in response')
            exit(0)

        logger.info('Login successful')

        config['auth'] = {'username': username, 'token': data['token']}
        config.save()

    except KeyboardInterrupt:
        logger.warn('Cancelled by user')
    except Exception as e:
        logger.error('Unable to login: ', exc_info=e)
