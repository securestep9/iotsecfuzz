import ast
import logging
from . import util

logger = logging.getLogger('isf')

param_types = {
    'string': str,
    'int': int,
    'float': float,
    'boolean': bool,
    'list': list,
    'dict': dict,
    'mac': util.MacAddress,
    'ipv4': util.IPv4
}


class ParameterValidationError(Exception):
    pass


class Parameter:

    def __init__(self, type, description, *, required=True, default=None,
                 values=None):
        self.type = type
        self.description = description
        self.required = required
        self.default = default if not required else None
        self.values = values

    def cast(self, value):
        """
        Coerce given value to the parameter type.

        :param value: value to coerce
        :return: coerced value on success
        """
        result = None
        try:
            if self.type in (
                    int, float, list, dict, tuple, bool) and isinstance(value,
                                                                        str):
                result = self.type(
                    ast.literal_eval(value))
            else:
                result = self.type(value)
        except ValueError:
            raise ParameterValidationError(
                'Unable to coerce value "%s" to type "%s"' % (
                    str(value), self.type.__name__))
        except TypeError:
            raise ParameterValidationError(
                'Type "%s" expected for value "%s"' % (
                    self.type.__name__, str(value)))
        return result


def param_from_dict(data):
    """
    Deserialize parameter object from dictionary.

    :param data: input dictionary
    :return: resulting parameter object
    """
    type = param_types[data['type']]
    description = data['description']
    required = data['required']
    values = None
    default = None
    if 'values' in data:
        values = data[values]
    if not required:
        default = data['default-value']
    return Parameter(type, description, required=required, default=default,
                     values=values)
