from ..command import Command
from ... import core


class CommandUse(Command):

    def __init__(self):
        super(CommandUse, self).__init__(name='use',
                                         description='Executes selected module',
                                         param_descriptions=['module name'],
                                         aliases=['select', 'sel'],
                                         min_args_number=1)

    def run(self, args):
        core.select_module(args[0])
