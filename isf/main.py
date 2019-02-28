import sys
import os
import argparse
import logging
from . import core
from . import console


sys.path.append(os.path.abspath('../'))

# Parse command line arguments

parser = argparse.ArgumentParser(prog='IoTSecFuzz',
                                 description='IoT testing framework')
parser.add_argument('--gui', action='store_true',
                    help='Run framework in GUI mode')
parser.add_argument('--dev', action='store_true',
                    help='Run framework in debug mode')
parser.add_argument('-D', '--module-dir', dest='paths', type=str,
                    action='append')
args = parser.parse_args()

if args.dev:
    os.environ['DEBUG'] = '1'
    core.logger.setLevel(logging.DEBUG)

if args.paths:
    core.modules_dirs.extend(args.paths)

# Add modules directories to PYTHONPATH
sys.path.extend(core.modules_dirs)


def main():
    if args.gui:
        pass
    else:
        console.start()
    return 0


if __name__ == '__main__':
    sys.exit(main())
