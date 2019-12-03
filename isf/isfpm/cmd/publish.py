from ...core import logger
from ..main import resolve_home_directory, get_config
from ..remote import RemotePackageRepository
from . import login
import base64
import hashlib
import requests
import os

description = 'publish built package to remote repository'


def add_arguments(parser):
    parser.add_argument('--scope', action='store', nargs='?',
                        help='scope to publish module to')


def run(args):
    try:
        resolve_home_directory()
        tarball = os.path.join(os.getcwd(), 'out', 'build.tar.gz')
        if not os.path.isfile(tarball):
            logger.error('No build file found')
            exit(0)

        config = get_config()

        if 'auth' not in config:
            login.run(None)

        if 'auth' not in config:
            return

        token = config['auth']['token']
        repo = RemotePackageRepository(config)

        logger.info('Reading build file')
        with open(tarball, 'rb') as tar:
            content = tar.read()
            encoded = base64.b64encode(content)

        if not encoded:
            logger.error('Unable to encode build file')
            exit(0)

        url = repo.repo_url + repo.urls['publish']
        logger.info('Uploading to %s' % url)
        payload = {'tarball': encoded.decode(),
                   'integrity': hashlib.sha256(content).hexdigest()}
        response = requests.post(url, json=payload,
                                 headers={
                                     'Authorization': 'JWT ' + token
                                 })
        try:
            data = response.json()
        except:
            data = {}
        if response.status_code != 200:
            logger.error('Unable to publish package: '
                         + (data['detail']
                            if 'detail' in data
                            else response.reason))
            exit(0)
        logger.info('Package published successfully')
    except KeyboardInterrupt:
        logger.warn('Publishing canceled')
    except Exception as e:
        logger.error('Publishing failed: ', exc_info=e)
