"""Manage path"""
import os

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


def path(*path_elements) -> str:
    """Return the path to an element from the ROOT directory of this project."""
    return os.path.join(CURRENT_DIR, *path_elements)


LOCALE_PATH = path('locale')
CONFIG_SCHEMA_PATH = path('config.schema')
FONT_DIR = path('fonts')


def font_path(*path_elements) -> str:
    """Return the path to an element from the font directory of this project."""
    return os.path.join(FONT_DIR, *path_elements)
