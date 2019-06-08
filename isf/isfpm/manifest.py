import json
import re
from semver import parse, valid_range
from .schema import validate
from .. import module
from .. import parameter

# TODO custom validation replace with JSON Schema

name_pattern = r'^[a-zA-Z0-9_-]{3,35}$'
qualified_name_pattern = r'^[a-zA-Z0-9_\\-\\/]{3,100}$'

description_schema = {
    'type': str,
    'required': True,
    'pattern': r'^[A-Za-z0-9 _.,!\"\'\$\&\;\?@ \x00]{0,80}$'
}

run_policy_schema = {
    'type': str,
    'required': False,
    'values': ['all', 'background-only', 'foreground-only']
}

output_params_schema = {
    'type': dict,
    'required': False,
    'key-pattern': r'^[a-zA-Z0-9_-]{1,20}$',
    'value-template': {
        'type': str,
        'pattern': r'^[a-zA-Z0-9_-]{0,80}$'
    }
}

param_schema = {
    'type': dict,
    'template': {
        'description': description_schema,
        'type': {
            'type': str,
            'required': True,
            'values': parameter.param_types.keys()
        },
        'values': {
            'type': list,
            'required': False,
            'validator': lambda obj, value: all(
                [type(el) is parameter.param_types[obj['type']] for el in
                 value])
        },
        'required': {
            'type': bool,
            'required': True,
        },
        'default-value': {
            'required': lambda obj: not obj['required'],
            'validator': lambda obj, value: value in obj['values']
            if 'values' in obj
            else type(value) is parameter.param_types[obj['type']]
        }
    }
}

input_params_schema = {
    'type': dict,
    'required': True,
    'key-pattern': r'^[a-zA-Z0-9_-]{1,20}$',
    'value-template': param_schema
}

submodule_schema = {
    'type': dict,
    'template': {
        'description': description_schema,
        'run-policy': run_policy_schema,
        'input': input_params_schema,
        'output': output_params_schema
    }
}


def submodules_validator(obj, value):
    if obj['type'] != 'container' or len(value) == 0:
        return False
    return all(
        [not set(obj['input'].keys()).intersection(set(sm['input'].keys())) for
         sm in value.values()])


manifest_schema = {
    'type': dict,
    'template': {
        'manifest-version': {
            'type': int,
            'required': True,
            'values': [1]
        },
        'name': {
            'type': str,
            'required': True,
            'pattern': name_pattern
        },
        'version': {
            'type': str,
            'required': True,
            'validator': lambda obj, value: parse(value,
                                                  loose=False) is not None
        },
        'category': {
            'type': str,
            'required': True,
            'values': module.CATEGORIES
        },
        'type': {
            'type': str,
            'required': False,
            'values': module.TYPES
        },
        'description': description_schema,
        'authors': {
            'type': list,
            'required': True,
            'validator': lambda obj, value: len(value) > 0 and all(
                [type(el) is str and bool(
                    re.match(r'^[a-zA-Z0-9_@ .-]{4,35}$', el)) for el in
                 value])
        },
        'keywords': {
            'type': list,
            'required': False,
            'validator': lambda obj, value: all(
                [bool(re.match(r'^[a-zA-Z0-9_@ .-]{4,35}$', el)) for el in
                 value])
        },
        'exclude': {
            'type': list,
            'required': False,
            'validator': lambda obj, value: all(
                [type(el) is str for el in value])
        },
        'run-policy': run_policy_schema,
        'license': {
            'type': str,
            'required': True,
            'pattern': r'^[a-zA-Z0-9_-]{0,35}$'
        },
        'input': input_params_schema,
        'output': output_params_schema,
        'submodules': {
            'type': dict,
            'required': lambda obj: 'type' in obj and obj[
                'type'] == 'container',
            'key-pattern': name_pattern,
            'value-template': submodule_schema,
            'validator': submodules_validator
        },
        'container-class': {
            'type': str,
            'required': lambda obj: 'type' in obj and obj[
                'type'] == 'container',
            'pattern': r'^[a-zA-Z0-9_]{0,35}$',
            'validator': lambda obj, value: obj['type'] == 'container'
        },
        'dependencies': {
            'type': dict,
            'required': True,
            'key-pattern': qualified_name_pattern,
            'value-template': {
                'type': str,
                'validator': lambda obj, value:
                valid_range(value, loose=False) is not None
            }
        },
        # TODO use actual environment setup
        'environment': {
            'type': dict,
            'required': False
        }
    }
}


def validate_manifest(manifest):
    validate(manifest_schema, manifest, member_path='manifest')


def load_manifest(path):
    with open(path) as manifest_file:
        manifest = json.load(manifest_file)
        validate_manifest(manifest)
        return manifest
