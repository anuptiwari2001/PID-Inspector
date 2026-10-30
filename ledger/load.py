import re

from ledger.autocad import load_autocad_csv, load_autocad_json
from ledger.common import failed_model
from ledger.loose import load_loose_xml
from ledger.pdftext import load_pdf
from ledger.proteus import load_proteus_xml
from ledger.xmlutil import local, parse_xml


def inspect_bytes(file_name: str, data: bytes):
    if not data:
        return failed_model(file_name, 0, "unknown", "The file is empty.", "Ledger")
    if len(data) > 12 * 1024 * 1024:
        return failed_model(file_name, len(data), "unknown", "Files larger than 12 MB are not opened here.", "Ledger")
    head = data[:1200].decode("utf-8", "replace").lstrip("\ufeff").lstrip()
    lower = file_name.lower()
    try:
        if lower.endswith(".pdf") or head.startswith("%PDF"):
            return load_pdf(file_name, data)
        text = data.decode("utf-8", "replace").lstrip("\ufeff")
        if lower.endswith(".json") or head.startswith("{") or head.startswith("["):
            return load_autocad_json(file_name, text, len(data))
        if lower.endswith(".csv"):
            return load_autocad_csv(file_name, text, len(data))
        if lower.endswith(".xml") or head.startswith("<") or head.startswith("<?xml"):
            return load_xml(file_name, text, len(data))
        return failed_model(file_name, len(data), "unknown", "Use a Proteus XML file, a Plant 3D JSON or CSV extract, or a PDF.", "Ledger")
    except Exception as error:
        return failed_model(file_name, len(data), "unknown", str(error) or "The file could not be read.", "Ledger")


def load_xml(file_name, text, byte_length):
    root, message = parse_xml(text)
    if root is None:
        if re.search(r"<DexpiModel\b", text, re.I):
            kind, parser = "dexpi2", "Ledger DEXPI 2 scan"
        elif re.search(r"<PlantModel\b", text, re.I):
            kind, parser = "proteus", "Ledger Proteus loader"
        else:
            kind, parser = "unknown", "Ledger"
        return failed_model(file_name, byte_length, kind, message, parser)
    name = local(root.tag)
    if name == "PlantModel":
        return load_proteus_xml(file_name, text, byte_length)
    spec = f"{root.attrib.get('specification', '')} {root.attrib.get('version', '')}"
    if name.lower().startswith("dexpi") or re.search(r"\b2(\.|$)", spec):
        return load_loose_xml(file_name, byte_length, root, "dexpi2")
    return load_loose_xml(file_name, byte_length, root, "unknown-root")
