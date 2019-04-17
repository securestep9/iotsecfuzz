from tabulate import tabulate
from prompt_toolkit import print_formatted_text, ANSI
from ..command import Command
from ... import core


class CommandOptions(Command):

    def __init__(self):
        super(CommandOptions, self).__init__(name='options',
                                             description='List input and ' +
                                                         'output parameters ' +
                                                         'for selected module',
                                             aliases=['params'])

    def run(self, args):
        curr_module = core.get_current_module()
        headers = ['\x1b[96m%s\x1b[0m' % s for s in
                   ['Name', 'Current value', 'Type',
                    'Required', 'Default value', 'Description']]
        items = [[n, core.module_input[
            n] if n in core.module_input else '\x1b[91m-\x1b[0m\x1b[97m',
                  p.type.__name__, p.required,
                  p.default if p.default else '\x1b[91m-\x1b[0m\x1b[97m',
                  p.description] for n, p in
                 curr_module.input.items()]
        core.logger.info('Module input parameters:')
        print()
        print_formatted_text(
            ANSI(tabulate(
                [['\x1b[97m%s\x1b[0m' % str(s) for s in row] for row in
                 items],
                headers=headers,
                tablefmt='psql')))
        print()
        if curr_module.output:
            headers = ['\x1b[96m%s\x1b[0m' % s for s in
                       ['Name', 'Description']]
            items = list(curr_module.output.items())
            core.logger.info('Module output parameters:')
            print_formatted_text(
                ANSI(tabulate(
                    [['\x1b[97m%s\x1b[0m' % str(s) for s in row] for row in
                     items],
                    headers=headers,
                    tablefmt='psql')))
            print()
