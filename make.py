"""
Generate translations and compile them!
"""
from pathlib import Path

import click
from babel.messages.frontend import CommandLineInterface as BabelCLI

BASE_DIR = Path(__file__).resolve().parent
TRANSLATION_DIR = BASE_DIR / 'locale'
TRANSLATION_DOMAIN = 'locale'
BABEL_CONFIG_FILE = BASE_DIR / 'babel.cfg'
MESSAGE_POT = TRANSLATION_DIR / 'message.pot'


@click.group()
def main():
    pass


def pybabel(*args):
    argv = ['']  # Add "command name", because, initialy, it's a command line

    for v in args:
        if not isinstance(v, str):
            argv.append(str(v))
        else:
            argv.append(v)

    BabelCLI().run(
        argv=argv
    )


def babel_extract():
    pybabel(
        'extract',
        '-F',
        BABEL_CONFIG_FILE,
        '-o',
        MESSAGE_POT,
        BASE_DIR,
    )


@main.command()
@click.option('-l', multiple=True, type=str, help='Creates or updates the message files for the given locale(s) (e.g. '
                                                  'pt_BR). Can be used multiple times. ')
def collect(**options):
    babel_extract()
    args = [
        'update',
        '-i',
        MESSAGE_POT,
        '-D',
        TRANSLATION_DOMAIN,
        '-d',
        TRANSLATION_DIR,
    ]

    for lang in options['l']:
        args.append('-l')
        args.append(lang)

    pybabel(*args)


# noinspection PyShadowingBuiltins
@main.command()
def compile():
    pybabel(
        'compile',
        '-D',
        TRANSLATION_DOMAIN,
        '-d',
        TRANSLATION_DIR,
    )


if __name__ == '__main__':
    main()
