import fnmatch
from ..main import exclude_patterns, root_whitelist, get_config, \
    resolve_home_directory
from ..remote import RemotePackageRepository
import os
from ...core import logger, collect_module_from_directory
import tarfile

description = 'generates production build for module'


def run(args):
    try:
        resolve_home_directory()
        config = get_config()
        repo = RemotePackageRepository(config)
        path = os.getcwd()
        collected = collect_module_from_directory(path)
        if not len(collected):
            raise ValueError('No modules found in current directory')
        qualified_name = list(collected.keys())[0]
        manifest = collected[qualified_name][0]
        logger.info('Packing module %s' % qualified_name)
        exclude = exclude_patterns[:]
        if 'exclude' in manifest:
            exclude += manifest['exclude']
        out_file = os.path.join(path, 'out', 'build.tar.gz')
        with tarfile.open(out_file, 'w:' + repo.config['compression']) as tar:
            for file in os.listdir(path):
                if file not in root_whitelist:
                    continue
                tar.add(file, filter=lambda f: f if not any(
                    [fnmatch.fnmatch(f.name, p) for p in exclude]) else None)
        logger.info('Packed into %s' % out_file)
    except KeyboardInterrupt:
        logger.warn('Build canceled')
    except Exception as e:
        logger.error('Build failed: ', exc_info=e)
