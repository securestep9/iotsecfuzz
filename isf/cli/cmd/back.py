from ..command import Command
from ... import core


class CommandBack(Command):

    def __init__(self):
        super(CommandBack, self).__init__(name='back',
                                          description=
                                          'Clears the current module')

    def run(self, args):
        core.current_module = None
