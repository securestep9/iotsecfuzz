import os
import subprocess

try:
    import isf.core
except ImportError:
    print('[!] Unable to import ISF module')
    print('[!] Make sure you have installed it correctly')
    exit(0)

$PYCHARM_DEBUG_CONFIG$

module_dir = os.path.dirname(
    os.path.dirname(os.path.realpath(__file__))).replace('\\', '\\\\')

env = os.environ.copy()
env['DEBUG'] = '1'

subprocess.run(['python', '-c',
                'import isf.main;import isf.core;'
                + 'isf.core.modules_dirs.append("' + module_dir + '");'
                + 'isf.main.main()'], env=env)
