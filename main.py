from typing import Union, Dict

import aenum
import click
import fpdf
import fpdf.drawing
import qrcode
import qrcode.image.svg

import myhack
from config import MyString, get_config_from_file
from i18n import _, get_translations, install_translation, DEFAULT_LANGUAGE
from layout import MARGIN, add_fonts, INTERLINE_SPACING, FONTS, ICONS, get_char_font_spec, Colors


class WifiSecurity(aenum.NamedConstant):
    """Select Wi-Fi security to use"""
    OPEN = 'Open'
    ENHANCED_OPEN = 'Enhanced Open'  # FYI : The kind of "Open" which comes with WPA3. It enables the encryption :D
    WEP = 'WEP'
    WPA = 'WPA Personal'
    WPA2PSK = 'WPA2 Personal'
    WPA2 = WPA2PSK
    WPA3PSK = 'WPA3 Personal'
    WPA3 = WPA3PSK

    @property
    def name(self):
        return self._name_

    @property
    def value(self):
        return self._value_

    @property
    def is_open(self):
        return self in [WifiSecurity.OPEN, WifiSecurity.ENHANCED_OPEN]

    @classmethod
    def from_string(cls, label: str):
        return cls._members_[label.upper().replace('-', '').replace(' ', '_')]

    def __eq__(self, other) -> bool:
        if isinstance(other, type(self)):
            other = other.value
        return self.value == other

    @classmethod
    @myhack.run_once
    def list(cls):
        return list(map(lambda x: x.name, cls))


@click.group('main')
@click.option('--colors', type=click.Choice(choices=Colors.list(), case_sensitive=False),
              default=Colors.default, callback=lambda _, __, x: Colors.from_string(x),
              help="Optimize colors for some kind of color-blind people, else it will be the most of people.")
@click.option('--lang', type=click.Choice(choices=get_translations(), case_sensitive=False),
              default=DEFAULT_LANGUAGE,
              help="Select the translation to use. By default, the one used is the one of the system "
                   "where this script is used.")
def main(colors: Colors, lang: str):
    colors.install()
    install_translation(lang)


@main.command('cli')
@click.option('--password', type=MyString(minlen=8, maxlen=63), required=False)
@click.option('--hidden', is_flag=True)
@click.argument('ssid', type=MyString(minlen=1))
@click.argument('security', type=click.Choice(WifiSecurity.list(), case_sensitive=False))
@click.argument('output', type=click.Path(exists=False, file_okay=True, dir_okay=False, writable=True))
def cli(ssid: str, security: WifiSecurity, output: str, password: str = None, hidden: bool = False) -> None:
    """Generate PDF with data in command line."""
    config = {
        ssid: {
            'security': security,
            'hidden': hidden
        }
    }
    if password is not None:
        config[ssid]['password'] = password
    return generate(config, output)


@main.command('generate')
@click.argument('config', type=click.File(mode="r", encoding='utf-8', lazy=True),
                callback=lambda _, __, config_io: get_config_from_file(config_io))
@click.argument('output', type=click.Path(exists=False, file_okay=True, dir_okay=False, writable=True))
def from_file(config: dict, output: str) -> None:
    """Generate PDF from a configuration file."""
    return generate(config, output)


def generate(config: dict, output: str) -> None:
    """Generate PDF"""
    pdf = fpdf.FPDF('P', 'pt', 'A4')
    pdf.set_margins(*MARGIN)

    # Setup metadata
    pdf.set_creator('gitlab.com/ajabep/wifi-print-readable-passwd')
    pdf.set_display_mode('fullpage')
    pdf.set_title(_('Wi-Fi QRCode'))

    # Setup fonts
    add_fonts(pdf)

    # Write wifi data
    wifi_characteristics: Dict[str, str]
    wifi_name: str
    for wifi_name, wifi_characteristics in config.items():
        wifi_characteristics = dict(**wifi_characteristics)
        wifi_characteristics.setdefault('ssid', wifi_name)
        wifi_characteristics['security'] = WifiSecurity.from_string(wifi_characteristics['security'])
        add_wifi(pdf, **wifi_characteristics)

    pdf.output(output, 'F')


def add_qr_code(pdf: fpdf.FPDF, ssid: str, security: WifiSecurity, password: Union[None, str] = None,
                hidden: bool = False):
    """Add a QRCode to a PDF."""

    def escape(clear: str):
        """Escape a string to be integrated into the string to generate the QRCode."""
        return clear \
            .replace('\\/', "\\\\") \
            .replace(':', "\\:") \
            .replace(';', "\\;") \
            .replace(',', "\\,") \
            .replace('\"', "\\\"")

    def get_qr_code_string() -> str:
        """Generate the string to encode as a QRCode to be authenticated to the Wi-Fi."""
        if security.is_open:
            sec = 'none'
        elif security == WifiSecurity.WEP:
            sec = 'WEP'
        elif security in [WifiSecurity.WPA, WifiSecurity.WPA2PSK]:
            sec = 'WPA'
        elif security == WifiSecurity.WPA3PSK:
            sec = 'SAE'
        else:
            raise NotImplementedError('Crap! A case which is not expected!')

        e_ssid = escape(ssid)

        if password is None:
            e_passwd = "None"  # nosec
        else:
            e_passwd = escape(password)

        hidden_str = ''
        if hidden:
            hidden_str = 'H:true;'

        return f"WIFI:S:{e_ssid};T:{sec};P:{e_passwd};{hidden_str}"

    qr = qrcode.QRCode(
        border=0,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        image_factory=qrcode.image.svg.SvgImage
    )
    qr.add_data(get_qr_code_string())
    qr.make(fit=True)
    pdf.set_fill_color(0, 0, 0)
    img = qr.make_image(
        fill_color="black",
        back_color="white"
    )

    width = pdf.w_pt - MARGIN[0] - MARGIN[2]
    svg_text = myhack.svg_abs_to_rel(img.to_string())
    svg = fpdf.svg.SVGObject(svg_text)
    svg.draw_to_page(pdf, MARGIN[0], MARGIN[1] * -1)  # * -1 == it pissed me off ; idk why 😠 ; help me plzzz
    pdf.set_y(pdf.get_y() + width + MARGIN[1] + INTERLINE_SPACING)  # width == height : QR Code are square


def add_wifi(pdf: fpdf.FPDF, ssid: str, security: WifiSecurity, password: Union[None, str] = None,
             hidden: bool = False):
    """Add a page with a Wi-Fi data in a PDF."""
    pdf.add_page()

    add_qr_code(pdf, ssid, security, password, hidden)

    main_font_fam = FONTS['main']['fam']
    main_font_size = FONTS['main']['size']
    about_font_fam = FONTS['about']['fam']
    about_font_size = FONTS['about']['size']
    icon_font_fam = FONTS['icons']['fam']
    icon_font_size = FONTS['icons']['size']
    pdf.set_text_color(0, 0, 0)

    pdf.set_font(icon_font_fam, size=icon_font_size)
    pdf.write(icon_font_size + INTERLINE_SPACING, ICONS['wifi'])
    pdf.set_font(main_font_fam, size=main_font_size)
    pdf.write(main_font_size + INTERLINE_SPACING, ' ' + ssid)
    pdf.ln()

    if security.is_open:
        pdf.set_text_color(0, 0, 0)
        pdf.set_font(icon_font_fam, size=icon_font_size)
        pdf.write(icon_font_size + INTERLINE_SPACING, ICONS['no_passwd'])
        pdf.set_font(main_font_fam, size=main_font_size)
        pdf.write(main_font_size + INTERLINE_SPACING, ' ')
        pdf.write(main_font_size + INTERLINE_SPACING, _('No password'))
    else:
        pdf.set_font(icon_font_fam, size=icon_font_size)
        pdf.write(icon_font_size + INTERLINE_SPACING, ICONS['passwd'])
        pdf.set_font(main_font_fam, size=main_font_size)
        pdf.write(main_font_size + INTERLINE_SPACING, ' ')
        write_password(pdf, password)

    if hidden:
        mid_page = pdf.w / 2
        rect_width = mid_page - INTERLINE_SPACING - (MARGIN[0] + MARGIN[2]) / 2
        r1_content_height = main_font_size + about_font_size + INTERLINE_SPACING
        r2_content_height = about_font_size * 3 + INTERLINE_SPACING * 2
        rect_content_height = max(r1_content_height, r2_content_height)
        rect_height = rect_content_height + INTERLINE_SPACING * 2

        margin_bottom = MARGIN[1]
        rect_org_y = pdf.h - margin_bottom - rect_height

        pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(0, 0, 0)

        r1 = {
            'org': fpdf.drawing.Point(MARGIN[0], rect_org_y),
            'size': fpdf.drawing.Point(rect_width, rect_height),
        }
        r2 = {
            'org': fpdf.drawing.Point(rect_width + MARGIN[0] + INTERLINE_SPACING * 2, rect_org_y),
            'size': fpdf.drawing.Point(rect_width, rect_height),
        }

        path: fpdf.drawing.PaintedPath
        with pdf.new_path() as path:
            for rect in [r1, r2]:
                path.add_path_element(
                    fpdf.drawing.RoundedRectangle(
                        corner_radii=fpdf.drawing.Point(rect_height / 4, rect_height / 4),
                        **rect
                    )
                )

        pdf.set_font(icon_font_fam, size=rect_content_height)
        r1_icon_width = pdf.get_string_width(ICONS['security'])
        pdf.text(
            r1['org'].x + INTERLINE_SPACING,
            rect_org_y + rect_content_height + INTERLINE_SPACING,  # Y coord to the bottom of the line
            ICONS['security']
        )
        r2_icon_width = pdf.get_string_width(ICONS['hidden'])
        pdf.text(
            r2['org'].x + INTERLINE_SPACING,
            rect_org_y + rect_content_height + INTERLINE_SPACING,
            ICONS['hidden']
        )

        pdf.set_font(about_font_fam)
        text_max_size(
            pdf,
            rect_width - INTERLINE_SPACING * 3 - r1_icon_width,
            about_font_size,
            r1['org'].x + INTERLINE_SPACING * 2 + r1_icon_width,
            rect_org_y + INTERLINE_SPACING + about_font_size,
            _('Security'),
            style="B"
        )
        pdf.set_font(main_font_fam)
        text_max_size(
            pdf,
            rect_width - INTERLINE_SPACING * 3 - r1_icon_width,
            main_font_size,
            r1['org'].x + INTERLINE_SPACING * 2 + r1_icon_width,
            rect_org_y + INTERLINE_SPACING + about_font_size + main_font_size,
            _("None") if security == WifiSecurity.OPEN else security.value
        )
        pdf.set_font(about_font_fam)
        text_max_size(
            pdf,
            rect_width - INTERLINE_SPACING * 3 - r2_icon_width,
            about_font_size,
            r2['org'].x + INTERLINE_SPACING + r2_icon_width,
            rect_org_y + INTERLINE_SPACING + about_font_size,
            _('Hidden Wi-Fi'),
            style="B"
        )
        text_max_size(
            pdf,
            rect_width - INTERLINE_SPACING * 3 - r2_icon_width,
            about_font_size,
            r2['org'].x + INTERLINE_SPACING + r2_icon_width,
            rect_org_y + INTERLINE_SPACING + about_font_size * 2,
            _('Not shown in the Wi-Fi list.'),
            max_line=2,
            interline=INTERLINE_SPACING,
        )


def text_max_size(pdf: fpdf.FPDF, width_text: int, max_font_size: int, x: float, y: float, text: str, max_line: int = 1,
                  interline: Union[None, int] = None, style: str = "") -> None:
    """
    Write a text with the maximum font size which will never go beyond a defined size.
    :param pdf: the FPDF object in which write
    :param width_text: the maximum width of the desired text.
    :param max_font_size: maximal font size to test
    :param x: where write the text (x-axis)
    :param y: where write the text (y-axis)
    :param text: the text to write
    :param max_line: If > 0, try to write the text on `max_line` lines.
    :param interline: the size of interline spaces
    :param style: the style to apply (`B`, `I`, `BI`, ``)
    """
    while max_font_size > 0:
        # Verify if we can write the text in only 1 line with the font size
        pdf.set_font(size=max_font_size, style=style)
        width = pdf.get_string_width(text)
        if width <= width_text:
            pdf.text(x, y, text)
            break

        # Else, try to wrap in line, and verify if it will be more than expected
        text_words = text.split(' ')
        lines = [[]]
        line_id = 0
        while len(text_words) > 0:
            new_word = text_words.pop(0)
            line_width = pdf.get_string_width(' '.join(lines[line_id] + [new_word]))
            if line_width <= width_text:
                lines[line_id].append(new_word)
            else:
                if line_id == max_line:
                    break
                line_id += 1
                lines.append([new_word])

        if len(text_words) == 0 and len(lines) <= max_line:
            # Ok, we found a valid configuration, let's write if !
            for line_id, line in enumerate(lines):
                pdf.text(
                    x,
                    y + interline + line_id * max_font_size,
                    ' '.join(line)
                )
            break

        # Ok, we have to try another font_size
        max_font_size -= 1

    if max_font_size == 0:
        raise NotImplementedError('This should never happen.')


def write_password(pdf: fpdf.FPDF, password: str):
    """Write the password with the right color and font(s) in a PDF."""
    for char in password:
        try:
            font_spec, font_color, char = get_char_font_spec(char)
        except Exception as e:
            raise click.ClickException(f"Char '{char}' (U+{ord(char)}) is not supported (yet) in WiFi password (so in "
                                       f"this program). ") from e

        font_family: str = FONTS[
            font_spec['font-id']
        ]['fam']
        font_size: int = FONTS[
            font_spec['font-id']
        ]['size']
        font_style: str = font_spec['style']

        pdf.set_font(font_family, font_style, font_size)
        pdf.set_text_color(*font_color)
        pdf.write(font_size + INTERLINE_SPACING, char)


if __name__ == '__main__':
    main()
