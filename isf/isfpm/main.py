from semver import max_satisfying
import requests


class Package:

    def __init__(self):
        self.dependencies = {}


class Node:
    def __init__(self, qualified_name, version_range):
        self.name = qualified_name
        self.version_ranges = [version_range]
        self.dependencies = []

    def add_edge(self, node):
        self.dependencies.append(node)


def resolve_node(node, resolved, unresolved=None):
    if unresolved is None:
        unresolved = {}
    unresolved[node.name] = node
    for dependency in node.dependencies:
        if dependency.name not in resolved:
            if dependency.name in unresolved:
                raise Exception('Circular dependencies found: %s -> %s' % (
                    node.name, dependency.name))
            resolve_node(dependency, resolved, unresolved)
        else:
            resolved[dependency.name].version_ranges.append(
                dependency.version_ranges[0])
    resolved[node.name] = node
    del unresolved[node.name]


def resolve_dependencies():
    pass
