import fnmatch
import os
from ...core import logger, collect_module_from_directory
import tarfile

description = 'generates production build for module'


def run(args):
    try:
        path = os.getcwd()
        collected = collect_module_from_directory(path)
        if not len(collected):
            raise ValueError('No modules found in current directory')
        qualified_name = list(collected.keys())[0]
        manifest = collected[qualified_name][0]
        logger.info('Packing module %s' % qualified_name)
        exclude_patterns = ['venv', '.idea', '.git', '*__pycache__', 'out',
                            '.isf']
        if 'exclude' in manifest:
            exclude_patterns += manifest['exclude']
        out_file = os.path.join(path, 'out', 'build.tar.xz')
        with tarfile.open(out_file, 'w:xz') as tar:
            for file in os.listdir(path):
                tar.add(file, filter=lambda f: f if not any(
                    [fnmatch.fnmatch(f.name, p) for p in
                     exclude_patterns]) else None)
        logger.info('Packed into %s' % out_file)
    except KeyboardInterrupt:
        logger.warn('Build canceled')
    except Exception as e:
        logger.error('Build failed: ', exc_info=e)
