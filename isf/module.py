import inspect
import core
import parameter
from enum import Enum
from util import CallbackIterator


class RunPolicy(Enum):
    ALL = 'all'
    BACKGROUND_ONLY = 'background-only'
    FOREGROUND_ONLY = 'foreground-only'


# Module categories
CATEGORIES = ['hardware', 'firmware', 'communication/arp',
              'communication/bluetooth', 'communication/nrf24',
              'communication/wifi', 'communication/zigbee', 'communication']
# Types of modules
TYPES = ['basic', 'container']


class Module:

    def __init__(self, manifest, location, py_module):
        self.manifest = manifest
        self.run_policy = RunPolicy(manifest['run-policy'])
        self.name = manifest['name']
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
        if inspect.isgenerator(self.run_method):
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
        if 'run-policy' in manifest['submodules'][name]:
            self.run_policy = manifest['submodules'][name]['run-policy']
        self.submodule_name = name
        self.container_class = getattr(py_module, manifest['container-class'])
        self.input = {key: parameter.param_from_dict(value) for key, value
                      in manifest['input'].items()}
        self.input.update(
            {key: parameter.param_from_dict(value) for key, value in
             manifest['submodules'][name]['input'].items()})

    def run(self, in_params):
        class_params = {key: in_params[key] for key in
                        self.manifest['input'].keys()}
        submodule_params = {key: in_params[key] for key in
                            self.manifest['submodules'][self.submodule_name][
                                'input'].keys()}
        container = self.container_class(**class_params)
        self.run_method = getattr(container, self.submodule_name)
        yield from super(Submodule, self).run(**submodule_params)
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
        for submodule_name in manifest[submodules].keys():
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
