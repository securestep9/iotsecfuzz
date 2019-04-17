from ..command import Command
from ... import core
from prompt_toolkit import print_formatted_text, ANSI
from tabulate import tabulate


class CommandSearch(Command):

    def __init__(self):
        super(CommandSearch, self).__init__(name='search',
                                            description='Finds module by name',
                                            param_descriptions=[
                                                'search string'],
                                            aliases=['find'],
                                            min_args_number=1)

    @staticmethod
    def highlight(string, substring):
        i = string.index(substring)
        return string[:i] + '\x1b[90;103m' + string[i:i + len(
            substring)] + '\x1b[0m\x1b[97m' + string[i + len(substring):]

    def run(self, args):
        found = list(filter(lambda m: args[0] in m[0], core.modules.items()))
        if not found:
            core.logger.warn('No results')
            return
        headers = ['\x1b[96m%s\x1b[0m' % s for s in
                   ['Name', 'Version', 'Authors', 'Description', 'Run policy']]
        items = [[self.highlight(n, args[0]), m.manifest['version'],
                  ','.join(m.manifest['authors']),
                  m.manifest['description'], m.run_policy] for n, m in
                 found]
        core.logger.info('Search results:')
        print()
        print_formatted_text(
            ANSI(tabulate(
                [['\x1b[97m%s\x1b[0m' % str(s) for s in row] for row in
                 items],
                headers=headers,
                tablefmt='psql')))
        print()
