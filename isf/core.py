import os
import logging
import semver
from . import module
from .worker import Worker
from .parameter import ParameterValidationError
from .isfpm.manifest import load_manifest


# Thrown if error occurs during module initialization
class ModuleLoadingError(Exception):
    pass


# Thrown if error occurs during module execution
class ModuleExecutionError(Exception):
    pass


# Create the logger

# Log messages as [time level]: message
LOGGING_FORMAT = '[%(asctime)s %(levelname)s]: %(message)s'
# Log time as dd-Mon-yyyy hh:mm:ss
LOGGING_DATE_FORMAT = '%H:%M:%S'

# Apply the config
logging.basicConfig(
    level=(logging.DEBUG if os.getenv('DEBUG') else logging.INFO),
    format=LOGGING_FORMAT, datefmt=LOGGING_DATE_FORMAT)

# Create the logger
logger = logging.getLogger('isf')

# Default path to load modules from
MODULES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'modules')

# List of paths to load modules from
modules_dirs = [MODULES_DIR]

# Dictionary where modules are stored
modules = {}


def collect_modules_from_directory(modules_dir):
    """
    Collect all valid modules from specified directory.

    :param modules_dir: base path to look for modules at
    :return:
    """
    categories_paths = list(filter(lambda f: os.path.isdir(f),
                                   [os.path.join(modules_dir, 'isf',
                                                 *p.split('/'))
                                    for p in module.CATEGORIES]))
    result = {}
    for category_dir in categories_paths:
        dirs = filter(lambda f: os.path.isdir(f),
                      [os.path.join(category_dir, p) for p in
                       os.listdir(category_dir)])
        for module_dir in dirs:
            if module_dir in categories_paths:
                continue
            manifest_path = os.path.join(module_dir, 'manifest.json')
            if os.path.isfile(manifest_path):
                manifest = None
                try:
                    manifest = load_manifest(manifest_path)
                except Exception as e:
                    logger.exception(
                        'Unable to load manifest file "%s"' % manifest_path,
                        exc_info=e)
                if manifest is None:
                    continue
                qualified_name = manifest['category'] + '/' + manifest['name']
                if os.path.basename(os.path.dirname(manifest_path)) != manifest[
                    'name']:
                    raise ModuleLoadingError(
                        'Module "%s" must be located in "%s" directory' % (
                            qualified_name,
                            os.path.join(*manifest['category'].split('/'))))
                logger.debug(
                    'Found a valid manifest file at "%s"' % manifest_path)
                result[qualified_name] = (manifest, manifest_path)
    return result


def check_modules_dependencies(installed_modules):
    """
    Remove all modules dependencies of which are not met.

    :param installed_modules: dictionary of installed modules
    :return: dictionary of modules that meet dependencies
    """
    result = {}
    for qualified_name, value in installed_modules.items():
        logger.debug('Checking dependencies for module %s' % qualified_name)
        unmet_dependencies = []
        manifest = value[0]
        for name in manifest['dependencies']:
            version = manifest['dependencies'][name]
            if name not in installed_modules:
                unmet_dependencies.append((name, 'not installed'))
            else:
                installed_version = installed_modules[name][0]['version']
                if not semver.satisfies(installed_version, version,
                                        loose=False):
                    unmet_dependencies.append((name, ('version "%s" does not '
                                                      + 'satisfy the required '
                                                      + 'range "%s') % (
                                                   installed_version, version)))
        if unmet_dependencies:
            logger.warning(
                'Found unmet dependencies for module %s:' % qualified_name)
            for dependency, message in unmet_dependencies:
                logger.warning(' - %s: %s' % (dependency, message))
            logger.warning('Module will not be loaded')
            logger.warning(
                'Please try running "isfpm update %s"' % qualified_name)
            continue
        logger.debug('Dependencies OK')
        result[qualified_name] = value
    return result


def load_modules():
    collected_modules = {}
    modules_to_load = {}

    # Collect modules from all paths
    logger.info('Collecting modules')
    for modules_dir in modules_dirs:
        collected_modules.update(collect_modules_from_directory(modules_dir))

    # Check dependencies
    modules_to_load = check_modules_dependencies(collected_modules)
    modules_loaded = 0
    submodules_loaded = 0
    logger.info('Identified %d modules to load' % len(modules_to_load))
    for qualified_name, value in modules_to_load.items():
        if qualified_name in modules:
            logger.info(
                'Module %s is already loaded, skipping' % qualified_name)
            continue
        logger.debug('Loading module %s' % qualified_name)
        fetched = {}
        try:
            fetched = module.load_modules(value[0], value[1])
        except Exception as e:
            logger.exception('Error loading module %s' % qualified_name,
                             exc_info=e)
        else:
            if len(fetched) > 1:
                # Submodules got loaded
                logger.debug('Loaded %d submodules from module %s:' % (
                    len(fetched.keys()), qualified_name))
                for key in fetched.keys():
                    logger.debug(' - %s' % key)
                submodules_loaded += len(fetched.keys())
            else:
                logger.debug('Module loaded successfully')
                modules_loaded += 1
            modules.update(fetched)

    logger.info('Successfully loaded %d modules and %d submodules' % (
        modules_loaded, submodules_loaded))


################################################################################
#                                                                              #
#                                                                              #
#                                                                              #
################################################################################

module_input = {}
current_module = None

workers = {}


def set_parameter(key, value):
    if not current_module:
        raise ParameterValidationError('No module selected')
    module_input[key] = current_module.validate_parameter(key, value)


def get_parameter(key):
    return module_input[key] if key in module_input else None


def run_current_module():
    if not current_module:
        raise ParameterValidationError('No module selected')

    if current_module.run_policy is module.RunPolicy.BACKGROUND_ONLY:
        raise ModuleExecutionError(
            'Module "%s" can only be run as background worker'
            % current_module.qualified_name)

    validated_params = current_module.validate_parameters(module_input)
    logger.debug('Running module %s' % current_module.qualified_name)
    yield from current_module.run(validated_params)


def start_worker():
    global current_module, module_input
    if not current_module:
        raise ParameterValidationError('No module selected')
    if current_module.qualified_name in workers:
        raise ModuleExecutionError(
            'Worker "%s" is already running' % current_module.qualified_name)

    if current_module.run_policy is module.RunPolicy.FOREGROUND_ONLY:
        raise ModuleExecutionError(
            'Module "%s" cannot be run in background' %
            current_module.qualified_name)
    validated_params = current_module.validate_parameters(module_input)
    worker = Worker(current_module, validated_params)
    workers[current_module.qualified_name] = worker
    worker.start()


def stop_worker(name):
    if name not in workers:
        raise ModuleExecutionError('No worker named "%s"' % name)
    workers[name].stop()


def select_module(name):
    global current_module, module_input
    if name not in modules:
        raise ModuleExecutionError('No module named "%s"' % name)
    module_input = {}
    current_module = modules[name]


def get_current_module():
    if not current_module:
        raise ParameterValidationError('No module selected')
    return current_module
