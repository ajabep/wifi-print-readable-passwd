"""Some quick&dirty hack because of incomplete ...implementations..."""
import io
import xml.etree.ElementTree  # nosec
from typing import List, Callable

import fpdf.svg
from defusedxml.ElementTree import fromstring as parse_xml_str

HEIGHT_ATTRS: List[str] = [
    'height',
    'y',
]
WIDTH_ATTRS: List[str] = [
    'width',
    'x',
]
NO_UNIT_ATTRS: List[str] = [
    'x',
    'y'
]


def run_once(f: Callable):
    """Wrapper to execute a function only once and return always the same result."""
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            wrapper.ret_val = f(*args, **kwargs)
        return wrapper.ret_val

    wrapper.has_run = False
    return wrapper


def svg_abs_to_rel(svg_text: str) -> str:
    """
    Change abs length to relatives to the viewbox
    :param svg_text: the SVG as a string
    :return: The scaled SVG, as a string
    """

    svg_root: xml.etree.ElementTree.Element = parse_xml_str(svg_text)
    viewbox = svg_root.get('viewBox')
    old_height = svg_root.get('height')
    old_width = svg_root.get('width')

    if viewbox is None and (old_height is None or old_width is None):
        raise Exception('Cannot scale: No viewbox AND no height nor width info')

    old_height = fpdf.svg.resolve_length(old_height)
    old_width = fpdf.svg.resolve_length(old_width)

    if viewbox is None:
        viewbox = [0, 0, old_height, old_width]
        svg_root.set('viewBox', ' '.join([str(i) for i in viewbox]))
    else:
        viewbox = [float(i) for i in viewbox.split(' ')]

    kw = viewbox[2] / old_width
    kh = viewbox[3] / old_height

    def fix_elem(element: xml.etree.ElementTree.Element):
        for key in element.keys():
            value = element.get(key)
            matchs = fpdf.svg.unit_splitter.fullmatch(value)
            if matchs is not None and matchs.group('unit') != '':
                value = fpdf.svg.resolve_length(value)

                if key in HEIGHT_ATTRS:
                    value *= kh
                if key in WIDTH_ATTRS:
                    value *= kw

                element.set(key, str(value))

    for elem in svg_root.iter():
        fix_elem(elem)
    del svg_root.attrib['width']
    del svg_root.attrib['height']

    with io.BytesIO() as out:
        etree = xml.etree.ElementTree.ElementTree(svg_root)
        etree.write(
            out,
            encoding='utf-8'
        )
        return str(out.getvalue(), 'utf-8')
