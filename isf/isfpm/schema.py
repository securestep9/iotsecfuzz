import re


class InvalidSchemaError(Exception):
    pass


class SchemaValidationError(Exception):
    pass


def validate(schema, instance, *, member_path='#', parent=None):
    if 'type' in schema:
        schema_type = schema['type']
        if type(instance) is not schema_type:
            raise SchemaValidationError(
                'Expected %s to be a "%s", but "%s" found' % (
                    member_path, schema_type.__name__, type(instance).__name__))
        if schema_type is str and 'pattern' in schema and not bool(
                re.match(schema['pattern'], instance)):
            raise SchemaValidationError(
                'Expected %s to match pattern /%s/' % (
                    member_path, schema['pattern']))
        elif schema_type is dict:
            if 'template' in schema:
                dict_template = schema['template']
                keys = dict_template.keys()
                for key in instance.keys():
                    if key not in keys:
                        raise SchemaValidationError(
                            '"%s" is not a valid member of object %s ' % (
                                key, member_path))
                for key in keys:
                    value_schema = dict_template[key]
                    if 'required' not in value_schema:
                        raise InvalidSchemaError(
                            'Missing "required" field in schema ' +
                            'for value "%s" in object %s' % (
                                key, member_path))
                    value_required = value_schema['required']
                    if callable(value_required):
                        value_required = value_required(instance)
                    if value_required and key not in instance:
                        raise SchemaValidationError(
                            'Object %s is missing required field "%s"' % (
                                member_path, key))
                    if key in instance:
                        validate(value_schema, instance[key],
                                 member_path=member_path + '.' + key,
                                 parent=instance)
            else:
                if 'key-pattern' in schema:
                    for key in instance.keys():
                        if not bool(re.match(schema['key-pattern'], key)):
                            raise SchemaValidationError(
                                ('Expected key names of %s to match ' +
                                 'pattern /%s/, but found "%s"') % (
                                    member_path, schema['key-pattern'],
                                    key))
                if 'value-template' in schema:
                    for key, value in instance.items():
                        validate(schema['value-template'], value,
                                 member_path=member_path + '.' + key,
                                 parent=instance)
    if 'values' in schema and instance not in schema['values']:
        raise SchemaValidationError('Expected member %s to be one of %s' % (
            member_path, schema['values']))
    if 'validator' in schema and not schema['validator'](parent, instance):
        raise SchemaValidationError('Invalid member %s' % member_path)
