from tabulate import tabulate
from prompt_toolkit import print_formatted_text, ANSI
from ..command import Command
from ... import core


class CommandList(Command):

    def __init__(self):
        super(CommandList, self).__init__(name='list',
                                          description='List all loaded modules')

    def run(self, args):
        headers = ['\x1b[96m%s\x1b[0m' % s for s in
                   ['Name', 'Version', 'Authors', 'Description', 'Run policy']]
        core.logger.info('Loaded modules:')
        items = [[n, m.manifest['version'], ','.join(m.manifest['authors']),
                  m.manifest['description'], m.run_policy] for n, m in
                 core.modules.items()]
        print()
        print_formatted_text(
            ANSI(tabulate(
                [['\x1b[97m%s\x1b[0m' % str(s) for s in row] for row in
                 items],
                headers=headers,
                tablefmt='psql')))
        print()
