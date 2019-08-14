import os
import inspect
from pathlib import Path

from . import core
from . import parameter
from enum import Enum
from .util import CallbackIterator
from .config import Configuration


class RunPolicy(Enum):
    ALL = 'all'
    BACKGROUND_ONLY = 'background-only'
    FOREGROUND_ONLY = 'foreground-only'


# Module categories
CATEGORIES = ['hardware', 'firmware', 'communication/tcpip',
              'communication/bluetooth', 'communication/nrf24',
              'communication/wifi', 'communication/zigbee', 'communication']
# Types of modules
TYPES = ['basic', 'container']


class Module:

    def __init__(self, manifest, location, py_module):
        self.manifest = manifest
        self.run_policy = RunPolicy(manifest['run-policy'])
        self.name = manifest['name']
        self.description = manifest['description']
        self.category = manifest['category']
        self.location = location
        self.input = None
        self.output = None
        self.py_module = py_module
        self.run_method = None
        self.qualified_name = None

    def validate_parameter(self, name, value):
        if name not in self.input:
            raise parameter.ParameterValidationError(
                'Module %s does not require parameter "%s"' % (
                    self.qualified_name, name))
        return self.input[name].cast(value)

    def validate_parameters(self, in_params):
        validated = {}
        for name, value in self.input.items():
            if name not in in_params:
                if value.required and not value.default:
                    raise core.ModuleExecutionError(
                        'Missing required parameter "%s"' % name)
                validated[name] = value.default
            else:
                validated[name] = value.cast(in_params[name])
        return validated

    def run(self, in_params):
        generator = None
        if inspect.isgeneratorfunction(self.run_method):
            generator = self.run_method(**in_params)
        else:
            generator = CallbackIterator(self.run_method,
                                         kwargs=in_params)
        yield from generator


class BasicModule(Module):

    def __init__(self, manifest, location, py_module):
        super(BasicModule, self).__init__(manifest, location, py_module)
        self.qualified_name = manifest['category'] + '/' + manifest['name']
        self.input = {key: parameter.param_from_dict(value) for key, value
                      in manifest['input'].items()}
        if 'output' in manifest:
            self.output = manifest['output']
        self.run_method = getattr(py_module, 'run')


class Submodule(Module):

    def __init__(self, manifest, name, location, py_module):
        super(Submodule, self).__init__(manifest, location, py_module)
        self.qualified_name = '%s/%s/%s' % (
            manifest['category'], manifest['name'], name)
        submodule_manifest = manifest['submodules'][name]
        if 'run-policy' in submodule_manifest:
            self.run_policy = RunPolicy(submodule_manifest['run-policy'])
        self.submodule_name = name
        self.description = submodule_manifest['description']
        self.container_class = getattr(py_module, manifest['container-class'])
        self.input = {key: parameter.param_from_dict(value) for key, value
                      in manifest['input'].items()}
        self.input.update(
            {key: parameter.param_from_dict(value) for key, value in
             submodule_manifest['input'].items()})

    def run(self, in_params):
        class_params = {key: in_params[key] for key in
                        self.manifest['input'].keys()}
        submodule_params = {key: in_params[key] for key in
                            self.manifest['submodules'][self.submodule_name][
                                'input'].keys()}
        container = self.container_class(**class_params)
        self.run_method = getattr(container, self.submodule_name)
        yield from super(Submodule, self).run(submodule_params)
        del self.run_method
        del container


def load_modules(manifest, location):
    module_path = ('isf/%s/%s'
                   % (manifest['category'], manifest['name'])).replace('/', '.')
    py_module = __import__(module_path, globals(), locals(), [], 0)
    for c in manifest['category'].split('/'):
        py_module = getattr(py_module, c)
    py_module = getattr(py_module, manifest['name'])

    if 'type' not in manifest:
        manifest['type'] = 'basic'
    if 'run-policy' not in manifest:
        manifest['run-policy'] = 'all'

    data_dir = os.path.join(core.DATA_DIR, *module_path.split('/')[1:])
    Path(data_dir).mkdir(parents=True, exist_ok=True)

    default_config = py_module.default_config \
        if hasattr(py_module, 'default_config') else None
    config_schema = py_module.config_schema \
        if hasattr(py_module, 'config_schema') else None

    config = Configuration(os.path.join(data_dir, 'config.json'),
                           config_schema, default_config)
    config.load()
    if default_config:
        config.save()

    # Set config & data directory attributes
    setattr(py_module, 'config', config)
    setattr(py_module, 'data_dir', data_dir)

    core.configs['.'.join(module_path.split('/'))] = config

    if manifest['type'] == 'basic':
        if not hasattr(py_module, 'run'):
            raise core.ModuleLoadingError(
                'Module %s/%s does not provide "run" function' % (
                    manifest['category'], manifest['name']))
        module = BasicModule(manifest, location, py_module)
        return {module.qualified_name: module}
    elif manifest['type'] == 'container':
        if not hasattr(py_module, manifest['container-class']):
            raise core.ModuleLoadingError(
                'Module %s/%s does not provide container class "%s"' % (
                    manifest['category'], manifest['name'],
                    manifest['container-class']))
        container_class = getattr(py_module, manifest['container-class'])
        submodules = {}
        for submodule_name in manifest['submodules'].keys():
            if not hasattr(container_class, submodule_name):
                raise core.ModuleLoadingError(
                    ('Module %s/%s does not provide '
                     + 'submodule "%s" in '
                     + 'container class "%s"') % (
                        manifest['category'],
                        manifest['name'],
                        submodule_name,
                        manifest['container-class']))
            submodule = Submodule(manifest, submodule_name, location, py_module)
            submodules[submodule.qualified_name] = submodule
        return submodules
