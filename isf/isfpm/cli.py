import sys
import re
import argparse
from .cmd import *

PREFIX = 'isf.isfpm.cmd.'
PATTERN = r'^isf\.isfpm\.cmd\.[^\.]+$'

command_names = [s.replace(PREFIX, '') for s in
                 filter(lambda m: re.match(PATTERN, m), sys.modules.keys())]

commands = {name: globals()[name] for name in command_names}

parser = argparse.ArgumentParser(prog='isfpm',
                                 description='IotSecFuzz Package Manager')
subparsers = parser.add_subparsers(help='action to perform', dest='command')
subparsers.required = True

for name, cmd in commands.items():
    if not hasattr(cmd, 'run') or not callable(cmd.run):
        raise ValueError(
            'CLI command "%s" does not override "run" method' % name)

    if not hasattr(cmd, 'description') or not isinstance(cmd.description, str):
        raise ValueError(
            'CLI command "%s" does not provide "description" property' % name)

    cmd_aliases = []
    if hasattr(cmd, 'aliases') and isinstance(cmd.aliases, list):
        cmd_aliases = cmd.aliases

    cmd_parser = subparsers.add_parser(name, help=cmd.description,
                                       aliases=cmd_aliases)

    if hasattr(cmd, 'add_arguments') and callable(cmd.add_arguments):
        cmd.add_arguments(cmd_parser)

    cmd_parser.set_defaults(run=cmd.run)


def main():
    args = parser.parse_args()
    args.run(args)


if __name__ == '__main__':
    sys.exit(main())
