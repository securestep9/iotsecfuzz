import pkgutil
import sys


def load_modules_from_directory(dir_name):
    for importer, package_name, is_pkg in pkgutil.walk_packages([dir_name]):
        if package_name not in sys.modules:
            importer.find_module(package_name).load_module(package_name)