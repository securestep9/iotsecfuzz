from abc import ABC, abstractmethod
from functools import cmp_to_key
import semver

ROOT_NODE_NAME = '__root'


class DependencyResolutionConflict(Exception):
    pass


class PackageRepository(ABC):

    @abstractmethod
    def get_versions(self, package_name):
        pass

    @abstractmethod
    def get_dependencies(self, package_name, package_version):
        pass


class PackageDependency:
    __slots__ = ['name', 'versions_range', 'max_satisfying',
                 'backtracked_due_to']

    def __init__(self, name, versions_range):
        self.name = name
        self.versions_range = versions_range
        self.max_satisfying = None
        self.backtracked_due_to = None


class PackageState:
    __slots__ = ['name', 'version', 'dependencies']

    def __init__(self, name, version):
        self.name = name
        self.version = version
        self.dependencies = {}


class PackageResolver:

    def __init__(self, dependencies, repository, installed_packages=None):
        self.repository = repository
        self.installed_packages = installed_packages \
            if installed_packages else {}
        self.root = ROOT_NODE_NAME
        self.state = {}
        root_state = PackageState(None, None)

        for name in dependencies:
            root_state.dependencies[name] = \
                PackageDependency(name, dependencies[name])

        self.state[self.root] = root_state
        self.queued_packages = list(dependencies.keys())
        self.queued_constraint_updates = []
        self.cached_versions = {}
        self.cached_dependencies = {}

    def clean_queued_packages(self):
        known_deps = list(self.state.keys())

        next_packages = known_deps.copy()

        for p in known_deps:
            deps = self.state[p].dependencies
            for key in deps.keys():
                if key not in next_packages:
                    next_packages.append(key)

        self.queued_packages = list(
            set(self.queued_packages) & set(next_packages))

    def clean_queued_constraint_updates(self):
        known_deps = list(self.state.keys())
        self.queued_constraint_updates = list(
            set(self.queued_constraint_updates) & set(known_deps))

    def drop_package(self, package):
        queued_packages = self.queued_packages
        if package in self.state:
            package_state = self.state[package]
            del self.state[package]
            dependencies = package_state.dependencies
            for dep in dependencies:
                self.drop_package(dep)
                queued_packages.append(dep)

    def update_constraints(self, package):
        state = self.state
        cached_dependencies = self.cached_dependencies
        if package in state:
            package_state = state[package]
            dependencies = cached_dependencies[package][package_state.version]
            package_state.dependencies = dependencies
            for dep in dependencies:
                self.drop_package(dep)
                self.queued_packages.append(dep)

    def max_satisfying(self, package):
        state = self.state
        versions = self.cached_versions[package]
        for installed_package in self.installed_packages:
            if package in installed_package.dependencies:
                versions.append(installed_package.dependencies[package])
        queued_packages = self.queued_packages
        nested_dependencies = {}
        for parent in state:
            package_state = state[parent]
            dependencies = package_state.dependencies
            if dependencies is None or package not in dependencies:
                continue
            dependency = dependencies[package]

            if dependency.max_satisfying is None:
                versions_range = dependency.versions_range
                max_satisfying = semver.max_satisfying(versions, versions_range)

                if max_satisfying is None:
                    backtracked_due_to = dependency.backtracked_due_to
                    constraining_package = ROOT_NODE_NAME
                    version = package_state.version
                    if version is not None:
                        constraining_package = package + '@' + version
                    if backtracked_due_to is not None:
                        msg = 'Unable to satisfy backtracked version' \
                              + ' constraint: %s@%s from %s due to shared ' \
                              + 'constraint on %s'
                        raise DependencyResolutionConflict(msg % (
                            package, versions_range, constraining_package,
                            backtracked_due_to))
                    else:
                        msg = 'Unable to satisfy version' \
                              + ' constraint: %s@%s from %s'
                        raise DependencyResolutionConflict(msg % (
                            package, versions_range, constraining_package))

                dependency.max_satisfying = max_satisfying

            nested_dependencies[parent] = dependency

        lowest_max_satisfying = None
        for parent in nested_dependencies:
            dependency = nested_dependencies[parent]
            max_satisfying = dependency.max_satisfying
            if lowest_max_satisfying is None:
                lowest_max_satisfying = {'parent': parent,
                                         'version': max_satisfying}
            if max_satisfying < lowest_max_satisfying['version']:
                lowest_max_satisfying['parent'] = parent
                lowest_max_satisfying['version'] = max_satisfying

        constraining_parent = lowest_max_satisfying['parent']
        version = lowest_max_satisfying['version']
        resolution_found = True

        for parent in nested_dependencies:
            dependency = nested_dependencies[parent]
            if parent != constraining_parent:
                versions_range = dependency.versions_range
                if not semver.satisfies(version, versions_range):
                    constraining_state = state[constraining_parent]
                    constrained_state = state[parent]
                    constrained_state_version = constrained_state.version
                    if constrained_state_version is None:
                        msg = 'Unable to satisfy version' \
                              + ' constraint: %s@%s from root due to shared ' \
                              + 'constraint from %s@%s'
                        raise DependencyResolutionConflict(msg % (
                            package, versions_range, constraining_parent,
                            constraining_state.version))
                    corrected_dependency = \
                        PackageDependency(parent,
                                          '<' + constrained_state_version)
                    corrected_dependency.backtracked_due_to = package
                    constraining_state.dependencies[
                        parent] = corrected_dependency
                    self.drop_package(parent)
                    queued_packages.append(parent)
                    resolution_found = False
                    break

        if resolution_found:
            return version

        return None

    def cache_version(self):
        cached_versions = self.cached_versions
        cached_packages = list(cached_versions.keys())
        to_cache = list(set(self.queued_packages) - set(cached_packages))
        versions = list(map(self.repository.get_versions, to_cache))
        for i in range(len(versions)):
            t = versions[i][:]
            t.sort(
                key=cmp_to_key(lambda a, b: semver.rcompare(a, b, loose=False)))
            cached_versions[to_cache[i]] = t

    def resolve_versions(self):
        queued_packages = self.queued_packages
        self.queued_packages = []
        next_queued_packages = self.queued_packages
        for package in queued_packages:
            if package not in next_queued_packages:
                version = self.max_satisfying(package)
                if version is not None:
                    self.state[package] = PackageState(package, version)
                    self.queued_constraint_updates.append(package)
        self.clean_queued_constraint_updates()

    def cache_dependencies(self):
        state = self.state
        cached_dependencies = self.cached_dependencies
        queued_constraint_updates = self.queued_constraint_updates
        dependencies_to_cache = []

        for package in queued_constraint_updates:
            version = state[package].version
            if package in cached_dependencies and version in \
                    cached_dependencies[package]:
                continue
            dependencies_to_cache.append(package)

        index = 0
        for dependencies in map(lambda p:
                                self.repository.get_dependencies(p, state[
                                    p].version), dependencies_to_cache):
            package = dependencies_to_cache[index]
            if package not in cached_dependencies:
                cached_dependencies[package] = {}
            to_map = cached_dependencies[package][
                state[package].version] = {}
            for dependency in dependencies:
                to_map[dependency] = PackageDependency(dependency, dependencies[
                    dependency])

            index += 1

    def refill_queues(self):
        queued_constraint_updates = list(set(self.queued_constraint_updates))
        self.queued_constraint_updates = []
        for package in queued_constraint_updates:
            self.update_constraints(package)
        self.clean_queued_packages()

    def resolve_queue(self):
        while True:
            self.cache_version()
            self.resolve_versions()
            self.cache_dependencies()
            self.refill_queues()
            if not len(self.queued_packages):
                break

    # Ah shit here we go again
    def resolve(self):
        self.resolve_queue()
        resolved = {}
        for package in self.state:
            resolved[package] = self.state[package].version
        del resolved[self.root]
        return resolved
