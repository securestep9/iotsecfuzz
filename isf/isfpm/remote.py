from .resolver import PackageRepository
import requests
from .. import core
from .schema import validate

repo_config_template = {
    'base': {
        'type': str,
        'required': False,
    },
    'urls': {
        'type': dict,
        'required': True,
        'template': {
            'packages': {
                'type': str,
                'required': True,
            },
            'publish': {
                'type': str,
                'required': True,
            },
            'auth': {
                'type': str,
                'required': True,
            }
        }
    },
    'compression': {
        'type': str,
        'required': True,
        'values': ['gz', 'xz']
    },
    'integrity': {
        'type': str,
        'required': True,
        'values': ['sha256']
    }
}

repo_config_schema = {
    'type': dict,
    'template': repo_config_template,
    'required': True
}


class RepositoryError(Exception):
    pass


class RemotePackageRepository(PackageRepository):

    def __init__(self, config):
        self.repo_url = config['repository']['url'].rstrip('/')
        self.config = config['repository']['config'] if 'config' in config[
            'repository'] else None
        if not self.config or self.config['base'] != self.repo_url:
            self.config = requests.get(self.repo_url + '/config.json').json()
            validate(repo_config_schema, self.config)
            self.config['base'] = self.repo_url
            config['repository']['config'] = self.config
            config.save()
        self.packages = {}
        self.urls = self.config['urls']

    def query_package(self, name):
        url = f'{self.repo_url}{self.urls["packages"]}{name}/'
        core.logger.debug('GET ' + url)
        response = requests.get(url)
        try:
            data = response.json()
        except:
            data = {}
        if response.status_code != 200:
            err = data['detail'] if 'detail' in data else response.reason
            raise RepositoryError(f'Package {name}: {err}')
        self.packages[name] = data

    def get_versions(self, package_name):
        if package_name not in self.packages:
            self.query_package(package_name)
        return list(self.packages[package_name]['versions'].keys())

    def get_dependencies(self, package_name, package_version):
        if package_name not in self.packages:
            self.query_package(package_name)
        if package_version not in self.packages[package_name]['versions']:
            raise RepositoryError('Package %s: no version %s found' % (
                package_name, package_version))
        return self.packages[package_name]['versions'][package_version][
            'manifest']['dependencies']
