from pkgutil import get_data
from pathlib import Path
import os
import subprocess
from ....core import logger
from ....console.logging import log_process_output


def get_project_file(dir, default):
    for file in os.listdir(dir):
        if file.endswith('.iml'):
            return os.path.join(dir, file)
    return os.path.join(dir, default)


def install_debugger_package(bin_path):
    logger.info('Installing pydevd_pycharm')
    install_proc = subprocess.Popen(
        [bin_path, '-m', 'pip', 'install', 'pydevd_pycharm'],
        env=os.environ, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

    result = log_process_output(install_proc, prefix='pip')

    if result != 0:
        raise RuntimeError('Unable to install required packages')


def init_pycharm_project(args, cwd, manifest, bin_path):
    logger.info('Generating PyCharm environment')
    logger.info('Creating project files')

    idea_dir = os.path.join(cwd, '.idea')
    Path(idea_dir).mkdir(parents=True, exist_ok=True)

    iml_path = get_project_file(idea_dir, manifest['name'] + '.iml')
    if not os.path.isfile(iml_path):
        iml_data = get_data('isf.resources',
                            'templates/project.iml.tpl').decode()
        with open(iml_path, 'wt', encoding='utf-8') as out:
            out.write(iml_data)

    ws_data = get_data('isf.resources',
                       'templates/workspace.xml.tpl').decode()
    ws_data = ws_data.replace('$SDK_HOME$', bin_path)
    ws_path = os.path.join(idea_dir, 'workspace.xml')

    with open(ws_path, 'wt', encoding='utf-8') as out:
        out.write(ws_data)

    vcs_data = get_data('isf.resources',
                        'templates/vcs.xml.tpl').decode()
    vcs_path = os.path.join(idea_dir, 'vcs.xml')

    if not args.no_git and not os.path.isfile(vcs_path):
        with open(vcs_path, 'wt', encoding='utf-8') as out:
            out.write(vcs_data)
