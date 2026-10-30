import re
import xml.etree.ElementTree as ET


def local(tag):
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def parse_xml(text):
    try:
        root = ET.fromstring(text)
    except ET.ParseError as error:
        line = getattr(error, "position", (None, None))[0]
        where = f" (line {line})" if line else ""
        return None, f"{error}{where}"
    return root, None


def namespace_of(text):
    match = re.search(r'\bxmlns(?::[\w.-]+)?\s*=\s*"([^"]+)"', text, re.I)
    return match.group(1) if match else None


def children(node):
    return list(node)


def walk_all(roots, visit):
    def go(node, path):
        tag = local(node.tag)
        ident = node.attrib.get("ID") or node.attrib.get("Id") or node.attrib.get("id")
        here = f"{path}/{tag}" + (f"[@ID='{ident}']" if ident else "")
        visit(node, here)
        for child in children(node):
            go(child, here)

    for node in roots:
        go(node, "")
