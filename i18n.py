"""
All the i18n/l10n stuff
"""
import gettext
import os
from typing import List

import locale
from myhack import run_once
from paths import LOCALE_PATH

DEFAULT_LANGUAGE = 'System'
GETTEXT_DOMAIN = 'locale'


def _(x: str) -> str:
    import builtins
    return builtins.__dict__.get('_', lambda x: x)(x)


@run_once
def get_translations() -> List[str]:
    """Return a list of available translations by listing the locale directory"""
    ret: List[str] = [
        DEFAULT_LANGUAGE
    ]
    i: os.DirEntry
    for i in os.scandir(LOCALE_PATH):
        if os.path.isfile(os.path.join(i.path, 'LC_MESSAGES', f'{GETTEXT_DOMAIN}.mo')):
            ret.append(i.name)
    return ret


@run_once
def install_translation(lang: str) -> None:
    """
    Create the `_` function.
    :param lang:
    """
    if lang == DEFAULT_LANGUAGE:
        lang = locale.getlocale()[0]

    if lang is None or lang == 'C':
        lang = 'en'

    locale.setlocale(locale.LC_ALL, lang)
    t = gettext.translation(
        GETTEXT_DOMAIN,
        LOCALE_PATH,
        languages=[lang]
    )
    t.install()
