from ledger.common import count_kinds, diagnostics_shell, warn
from ledger.xmlutil import local, walk_all

TAG_ATTRS = ["tagName", "TagName", "tag", "Tag", "lineNumber", "LineNumber"]


def kind_from_name(name):
    value = name.lower()
    if "valve" in value:
        return "valve"
    if "instrument" in value:
        return "instrument"
    if "nozzle" in value:
        return "nozzle"
    if "piping" in value or "pipeline" in value or "segment" in value:
        return "piping"
    if any(word in value for word in ("equipment", "pump", "vessel", "exchanger", "tank", "column")):
        return "equipment"
    return "other"


def attrs_of(node):
    return dict(node.attrib)


def load_loose_xml(file_name, byte_length, root, mode):
    diagnostics = diagnostics_shell(file_name, byte_length, "dexpi2" if mode == "dexpi2" else "unknown")
    root_name = local(root.tag) if root is not None else "unknown"
    root_attrs = attrs_of(root) if root is not None else {}
    diagnostics["parserName"] = "Ledger DEXPI 2 scan" if mode == "dexpi2" else "Ledger XML scan"
    diagnostics["formatVersion"] = root_attrs.get("specification") or root_attrs.get("version") or None
    diagnostics["formatLabel"] = (
        f"DEXPI {diagnostics['formatVersion'] or '2.x'} (best effort)"
        if mode == "dexpi2"
        else f"XML root <{root_name}>"
    )
    diagnostics["scopeNotes"] = [
        "Only elements with an explicit tag attribute were kept. Identifiers were not promoted to tags.",
        "No relationships were interpreted. Connection checks are skipped so a parser gap is not reported as an open line.",
    ]
    if mode == "dexpi2":
        warn(
            diagnostics["warnings"],
            "dexpi2-unsupported",
            "This file looks like DEXPI 2.x. The structured loader targets Proteus XML (DEXPI 1.3/1.4). DEXPI 2.0.1 needs its own parser.",
            "Tags below are a best-effort scan. Missing relationships are an import limit, not a drawing defect.",
        )
    else:
        warn(
            diagnostics["warnings"],
            "root-unsupported",
            f"The root element is <{root_name}>, not PlantModel. A best-effort tag scan was used instead of the Proteus loader.",
        )

    objects = []
    used = set()

    def visit(node, path):
        attrs = attrs_of(node)
        tag_value = ""
        for key in TAG_ATTRS:
            if (attrs.get(key) or "").strip():
                tag_value = attrs[key].strip()
                break
        if not tag_value:
            return
        element = local(node.tag)
        raw_id = (attrs.get("id") or attrs.get("ID") or attrs.get("Id") or f"{element}-{len(objects) + 1}").strip()
        ident = raw_id
        if ident in used:
            ident = f"{raw_id}~{len(objects) + 1}"
        used.add(ident)
        objects.append({
            "id": ident,
            "tag": tag_value,
            "kind": kind_from_name(element),
            "objectType": element,
            "componentName": None,
            "properties": [],
            "connections": [],
            "parentId": None,
            "reviewStatus": "native",
            "confidence": None,
            "page": None,
            "location": None,
            "sourceElement": element,
            "sourcePath": path,
            "drawing": None,
            "hint": "Best-effort tag scan. Attributes other than the tag were not mapped.",
        })

    if root is not None:
        walk_all([root], visit)
    if not objects:
        warn(diagnostics["warnings"], "no-tags", "No tag attributes were found. Nothing was placed in the check set.")
    diagnostics["objectCount"] = len(objects)
    diagnostics["countsByKind"] = count_kinds(objects)
    return {"diagnostics": diagnostics, "objects": objects, "edges": [], "candidates": [], "transcript": []}
