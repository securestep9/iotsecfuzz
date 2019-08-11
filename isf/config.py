import json
import os
from .isfpm.schema import validate


class Configuration:

    def __init__(self, path, schema=None, default=None):
        self.schema = schema
        self.path = path
        self.default = default if default else None
        self.data = None

    def save(self):
        if self.schema is not None:
            validate(self.data, self.schema)
        with open(self.path, 'wt', encoding='utf-8') as out_file:
            json.dump(self.data, out_file, indent=4)

    def load(self):
        if os.path.isfile(self.path):
            try:
                with open(self.path, 'rt', encoding='utf-8') as in_file:
                    data = json.load(in_file)
                if self.schema is not None:
                    validate(self.schema, data)
                self.data = data
            except:
                self.data = self.default
        else:
            self.data = self.default

    def get_data(self):
        return self.data

    def __getitem__(self, item):
        """
        An alias to get_data()[item].
        :param item: key
        :return: corresponding value
        """
        return self.data[item]

    def __setitem__(self, key, value):
        """
        An alias to get_data()[key] = value
        :param key: dictionary key
        :param value:
        :return:
        """
        self.data[key] = value

    def to_json(self):
        return json.dumps(self.data)

    def from_json(self, json_str):
        data = json.loads(json_str)
        if self.schema is not None:
            validate(self.schema, data)
        self.data = data
