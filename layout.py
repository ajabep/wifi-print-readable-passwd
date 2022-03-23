"""
All which is about the layout
"""
import string
from typing import Dict, Tuple, Union

import aenum
import fpdf

import myhack
from paths import font_path

CM_TO_PT = 72 / 2.54
INTERLINE_SPACING = 4
FONT_SPECT_TYPE = Dict[str, str | int]
FONTS: Dict[str, FONT_SPECT_TYPE] = {
    'main': {
        'fam': 'NotoSans',
        'size': 25,
    },
    'about': {
        'fam': 'NotoSans',
        'size': 14,
    },
    'mono': {
        'fam': 'PTMono',
        'size': 25,
    },
}
FONTS |= {
    'icons': {
        'fam': 'Icons',
        'size': FONTS['main']['size']
    },
    'space': {
        'fam': 'FiraCode',
        'size': FONTS['mono']['size']
    },
}
COLOR_TYPE = Tuple[int, int, int]  # RGB
COLORDICT_TYPE = Dict[str, COLOR_TYPE]
COLORS: Union[COLORDICT_TYPE, None] = None
TYPO_SPEC_TYPE = Dict[str, str]
TYPOS_PASSWORD: Dict[str, TYPO_SPEC_TYPE] = {
    'numbers': {
        'font-id': 'mono',  # ID in the `FONTS` dict
        'style': '',
    },
    'lower': {
        'font-id': 'mono',
        'style': '',
    },
    'upper': {
        'font-id': 'mono',
        'style': '',
    },
    'space': {
        'font-id': 'space',
        'style': '',
    },
    'special': {
        'font-id': 'mono',
        'style': '',
    }
}
ICONS: Dict[str, str] = {
    'wifi': '\ue63e',
    'passwd': '\ue897',
    'hidden': '\ue8f5',
    'security': '\ue32a',
    'no_passwd': '\ue641',
}
MARGIN = (2 * CM_TO_PT, 2 * CM_TO_PT, 2 * CM_TO_PT)


def add_fonts(pdf: fpdf.FPDF) -> None:
    """Include fonts into the PDF file"""
    pdf.add_font('Icons', '', font_path('material-design-icons-4.0.0', 'font', 'MaterialIcons-Regular.ttf'), True)

    pdf.add_font('NotoSans', '', font_path('NotoSans', 'NotoSans-Regular.ttf'), True)
    pdf.add_font('NotoSans', 'B', font_path('NotoSans', 'NotoSans-Bold.ttf'), True)
    pdf.add_font('NotoSans', 'I', font_path('NotoSans', 'NotoSans-Italic.ttf'), True)
    pdf.add_font('NotoSans', 'BI', font_path('NotoSans', 'NotoSans-BoldItalic.ttf'), True)

    pdf.add_font('PTMono', '', font_path('PTMono', 'PTMono-Regular.ttf'), True)

    pdf.add_font('Firacode', '', font_path('FiraCode6.2', 'ttf', 'FiraCode-Regular.ttf'), True)


def get_char_font_spec(char: str) -> Tuple[TYPO_SPEC_TYPE, COLOR_TYPE, str]:
    """
    Determine the specification of the font for a char
    :param char: the char
    :return: A tuple of (
        1. the spec of the typo
        2. the color
        3. the char (if it has to be displayed by another one)
    )
    """
    if char in string.digits:
        char_type = 'numbers'
    elif char in string.ascii_lowercase:
        char_type = 'lower'
    elif char in string.ascii_uppercase:
        char_type = 'upper'
    elif char == ' ':
        char_type = 'space'
        char = '␣'
    elif char in string.printable:
        char_type = 'special'
    else:
        raise Exception(f"Char '{char}' (unicode codepoint {ord(char)}) is not supported (yet) in WiFi password (so in "
                        f"this program). ")

    return TYPOS_PASSWORD[char_type], COLORS[char_type], char


class Colors(aenum.NamedConstant):
    """Select colors"""
    EVERYONE = {
        'upper': (0x0c, 0x52, 0x75),
        'lower': (0x09, 0x7d, 0xb8),
        'numbers': (0xb3, 0x30, 0x00),
        'special': (0x09, 0xb8, 0x32),
        'space': (0x09, 0xb8, 0x32),
    }

    DEUTERANOPIA = {
        'upper': (0x55, 0x5e, 0x75),
        'lower': (0x5f, 0x7d, 0xbb),
        'numbers': (0x00, 0x51, 0xb0),
        'special': (0xaa, 0x99, 0x40),
        'space': (0xaa, 0x99, 0x40),
    }
    PROTANOPIA = DEUTERANOPIA

    TRITANOPIA = {
        'upper': (0x00, 0x70, 0x6e),
        'lower': (0x00, 0xa9, 0xa5),
        'numbers': (0xfd, 0x00, 0x13),
        'special': (0xcd, 0x5e, 0x8e),
        'space': (0xcd, 0x5e, 0x8e),
    }

    BLACK_WHITE = {
        'upper': (0x00, 0x00, 0x00),
        'lower': (0x25, 0x25, 0x25),
        'numbers': (0x50, 0x50, 0x50),
        'special': (0x75, 0x75, 0x75),
        'space': (0x75, 0x75, 0x75),
    }

    @property
    def name(self):
        return self._name_

    @property
    def value(self):
        return self._value_

    @classmethod
    def default(cls):
        return cls.EVERYONE

    @classmethod
    def from_string(cls, label: str):
        return cls._members_[label.upper()]

    def __eq__(self, other) -> bool:
        print(self.__dict__)
        if not isinstance(other, type(self)):
            return self.value == other
        return self.value == other.value and self.name == other.name

    @classmethod
    @myhack.run_once
    def list(cls):
        return list(map(lambda x: x.name, cls))

    def install(self):
        """Define the color set defined in `self` as the one to use"""
        global COLORS
        COLORS = self.value

    def casefold(self) -> str:
        return self.name.casefold()
