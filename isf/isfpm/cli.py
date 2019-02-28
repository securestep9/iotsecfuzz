import sys
from .cmd import *

PREFIX = 'isf.isfpm.cmd.'

command_names = [s.replace(PREFIX, '') for s in
                 filter(lambda m: m.startswith(PREFIX), sys.modules.keys())]

commands = {name: globals()[name] for name in command_names}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in command_names:
        print('Usage: isfpm <command>')
        print()
        print('where <command> is one of: ')
        for cmd in command_names:
            print('  %s' % cmd)
        print()
    else:
        commands[sys.argv[1]].run()


if __name__ == '__main__':
    sys.exit(main())
