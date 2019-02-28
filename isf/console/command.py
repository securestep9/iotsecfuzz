from abc import abstractmethod


class Command:

    def __init__(self, *, name, description, param_descriptions=None,
                 aliases=None, min_args_number=0):
        if param_descriptions is None:
            param_descriptions = []
        if aliases is None:
            aliases = []
        self.name = name
        self.description = description
        self.aliases = aliases
        self.param_descriptions = param_descriptions
        self.min_args_number = min_args_number

    @abstractmethod
    def run(self, args):
        pass
