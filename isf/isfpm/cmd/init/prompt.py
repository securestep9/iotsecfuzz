from prompt_toolkit import prompt, HTML
from ....core import logger, module
import semver
import json

prompt_template = '<a fg="#8E33CE">[?]</a> <a fg="#FFFFFF">%s: </a>'


def prompt_password(text):
    return prompt(HTML(prompt_template % text), is_password=True)


def prompt_any(question):
    return prompt(HTML(prompt_template % question))


def prompt_data(name, default):
    data = prompt(HTML(prompt_template % (
            'Enter module %s (%s)' % (name, default))))
    return data if data else default


def prompt_authors(default):
    author = prompt(HTML(prompt_template % (
            'Enter module author\'s name (%s)' % default)))
    return [author] if author else [default]


def prompt_description():
    desc = prompt(HTML(prompt_template % 'Enter module description'))
    return desc if desc else ''


def prompt_version(default):
    while True:
        version = prompt(
            HTML(prompt_template % ('Enter module version (%s)' % default)))
        if version and semver.parse(version, loose=False) is None:
            logger.warn('Please check your input.')
            logger.warn('Version must be a valid semver.')
        else:
            return version if version else default


def prompt_category(default):
    while True:
        category = prompt(
            HTML(prompt_template % ('Enter module category (%s)' % default)))
        if category and category not in module.CATEGORIES:
            logger.warn('Please check your input.')
            logger.warn('Category should be one of: ')
            print(json.dumps(module.CATEGORIES, indent=4))
        else:
            return category if category else default
