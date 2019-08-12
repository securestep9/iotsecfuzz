import os
import subprocess

try:
    import isf.core
except ImportError:
    print('[!] Unable to import ISF module')
    print('[!] Make sure you have installed it correctly')
    exit(0)

module_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
home_dir = os.path.join(module_dir, '.isf')

module_dir = module_dir.replace('\\', '\\\\')
home_dir = home_dir.replace('\\', '\\\\')

subprocess.run(['python', '-c',
                'import isf.main;import isf.core; '
                + 'isf.core.HOME_DIR = "' + home_dir + '";'
                + 'isf.core.modules_dirs.append("' + module_dir + '");'
                + 'isf.main.main()'])
