import sys
import os
import argparse
import logging
from . import core
from . import console

# Parse command line arguments

parser = argparse.ArgumentParser(prog='isf',
                                 description='IoT testing framework')
parser.add_argument('--gui', action='store_true',
                    help='run framework in GUI mode')
parser.add_argument('--dev', action='store_true',
                    help='run framework in debug mode')
parser.add_argument('--home', type=str, help='framework home directory')
parser.add_argument('-D', '--module-dir', dest='paths', type=str,
                    action='append')
args = parser.parse_args()

if args.dev:
    os.environ['DEBUG'] = '1'
    core.logger.setLevel(logging.DEBUG)


def main():

    core.init_home_directory(args.home)

    if args.paths:
        core.modules_dirs.extend(args.paths)

    if args.gui:
        pass
    else:
        console.start()
    return 0


if __name__ == '__main__':
    sys.exit(main())
