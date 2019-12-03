import requests
from prompt_toolkit import print_formatted_text, ANSI
from tabulate import tabulate
from ..main import get_config, resolve_home_directory
from ..remote import RemotePackageRepository
from ...core import logger

description = 'get list of modules in remote repository'


def run(args):
    try:
        resolve_home_directory()
        config = get_config()
        repo = RemotePackageRepository(config)
        url = repo.repo_url + repo.urls['packages']
        logger.info('Collecting packages info from ' + url)
        data = requests.get(url).json()

        headers = ['\x1b[96m%s\x1b[0m' % s for s in
                   ['Name', 'Latest version']]
        logger.info('Available modules:')
        items = [[m['category'] + '/' + m['name'], m['latest']] for m in data]
        print()
        print_formatted_text(
            ANSI(tabulate(
                [['\x1b[97m%s\x1b[0m' % str(s) for s in row] for row in
                 items],
                headers=headers,
                tablefmt='psql')))

        print()

    except KeyboardInterrupt:
        logger.warn('Operation canceled')
    except Exception as e:
        logger.error('Error: ', exc_info=e)
