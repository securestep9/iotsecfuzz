from tabulate import tabulate
from prompt_toolkit import print_formatted_text, ANSI
from ..command import Command
from .. import console
from ... import core


class CommandHelp(Command):

    def __init__(self):
        super(CommandHelp, self).__init__(name='help',
                                          description='List available commands')

    def run(self, args):
        aliases = sum(
            [console.commands[cmd].aliases for cmd in console.commands], [])
        commands = filter(lambda cmd: cmd not in aliases, console.commands)
        headers = ['\x1b[96m%s\x1b[0m' % s for s in
                   ['Name', 'Parameters', 'Description', 'Aliases'.center(20)]]
        core.logger.info('Available commands:')
        items = [[cmd, ', '.join(console.commands[cmd].param_descriptions),
                  console.commands[cmd].description,
                  ', '.join(console.commands[cmd].aliases)] for cmd in commands]
        print()
        print_formatted_text(
            ANSI(tabulate(
                [['\x1b[97m%s\x1b[0m' % str(s) for s in row] for row in
                 items],
                headers=headers,
                tablefmt='psql')))
        print()
