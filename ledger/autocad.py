import json
import re

from ledger.common import count_kinds, diagnostics_shell, failed_model, label_for, warn

SCOPE = [
    "AutoCAD Plant 3D has no direct P&ID XML export. This adapter maps a JSON or CSV extract from the Plant SDK or Data Manager.",
    "Classes and property names are taken as exported. They are not rewritten into Proteus class names.",
    "A connection is recorded only when the extract lists the other handle. Nothing is inferred from a drawing.",
]


def kind_from_class(class_name):
    value = class_name.lower()
    if re.search(r"valve|check|gate|globe|ball|butterfly", value):
        return "valve"
    if re.search(r"instrument|transmitter|indicator|gauge|controller|meter", value):
        return "instrument"
    if "nozzle" in value:
        return "nozzle"
    if re.search(r"line|pipe|segment|piping", value):
        return "piping"
    if re.search(r"pump|vessel|exchanger|tank|column|compressor|equipment|filter|drum|heater|cooler", value):
        return "equipment"
    return "other"


def property_of(name, value):
    if value is None:
        return {"name": name, "label": label_for(name), "value": None, "status": "uninterpreted"}
    return {"name": name, "label": label_for(name), "value": value, "status": "blank" if value.strip() == "" else "ok"}


def link_handles(objects, links):
    edges = []
    seen = set()
    for link in links:
        if not link["targetId"]:
            continue
        key = "|".join(sorted([link["ownerId"], link["targetId"]]))
        if key in seen:
            continue
        seen.add(key)
        edges.append({
            "id": f"edge-{len(edges) + 1}",
            "ownerId": link["ownerId"],
            "fromId": link["ownerId"],
            "toId": link["targetId"],
            "sourcePath": link["sourcePath"],
        })
    by_id = {obj["id"]: obj for obj in objects}
    for edge in edges:
        for ident, other in ((edge["fromId"], edge["toId"]), (edge["toId"], edge["fromId"])):
            obj = by_id.get(ident)
            if not obj or not other or any(item["targetId"] == other for item in obj["connections"]):
                continue
            target = by_id.get(other)
            obj["connections"].append({"targetId": other, "targetTag": target["tag"] if target else None, "relation": "extract-link"})
    return edges


def finish(file_name, byte_length, source_kind, parser_name, format_label, drawing_name, originating, raw, warnings):
    diagnostics = diagnostics_shell(file_name, byte_length, source_kind)
    diagnostics["parserName"] = parser_name
    diagnostics["formatLabel"] = format_label
    diagnostics["drawingName"] = drawing_name
    diagnostics["originatingSystem"] = originating
    diagnostics["scopeNotes"] = list(SCOPE)
    for item in warnings:
        warn(diagnostics["warnings"], item["code"], item["message"], item.get("detail"))
    objects = []
    for item in raw:
        objects.append({
            "id": item["id"],
            "tag": item["tag"],
            "kind": kind_from_class(item["className"]) if item["className"] else "other",
            "objectType": item["className"],
            "componentName": None,
            "properties": item["properties"],
            "connections": [],
            "parentId": None,
            "reviewStatus": "native",
            "confidence": None,
            "page": None,
            "location": None,
            "sourceElement": item["className"] or "Row",
            "sourcePath": item["path"],
            "drawing": drawing_name,
            "hint": None,
        })
    edges = link_handles(objects, [
        {"ownerId": item["id"], "targetId": target, "sourcePath": item["path"]}
        for item in raw
        for target in item["connections"]
    ])
    diagnostics["objectCount"] = len(objects)
    diagnostics["countsByKind"] = count_kinds(objects)
    return {"diagnostics": diagnostics, "objects": objects, "edges": edges, "candidates": [], "transcript": []}


def load_autocad_json(file_name, text, byte_length):
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as error:
        return failed_model(file_name, byte_length, "autocad-json", str(error), "Ledger Plant 3D JSON adapter")
    root = parsed if isinstance(parsed, dict) else None
    listing = parsed if isinstance(parsed, list) else (root or {}).get("objects")
    if not isinstance(listing, list):
        return finish(file_name, byte_length, "autocad-json", "Ledger Plant 3D JSON adapter", "JSON", None, "AutoCAD Plant 3D", [], [{
            "code": "json-shape",
            "message": "This JSON has no objects array. Expected an SDK or Data Manager style extract.",
        }])
    warnings = []
    raw = []
    for index, entry in enumerate(listing):
        if not isinstance(entry, dict):
            warnings.append({"code": "json-row", "message": f"Object {index + 1} is not a record and was skipped."})
            continue
        ident = str(entry.get("id") or entry.get("handle") or entry.get("Handle") or "").strip()
        if not ident:
            warnings.append({"code": "json-row", "message": f"Object {index + 1} has no id or handle and was skipped."})
            continue
        class_name = str(entry.get("className") or entry.get("class") or entry.get("Class") or "").strip()
        if not class_name:
            warnings.append({"code": "json-class", "message": f"{ident} has no class name. It was kept as an unclassified object."})
        tag_raw = entry["tag"] if "tag" in entry else entry.get("Tag")
        tag = None if tag_raw is None else (str(tag_raw).strip() or None)
        properties = []
        bag = entry.get("properties") if isinstance(entry.get("properties"), dict) else {}
        for name, value in bag.items():
            if value is None or not isinstance(value, (str, int, float, bool)):
                properties.append(property_of(name, None))
            else:
                properties.append(property_of(name, str(value)))
        connections = [str(item).strip() for item in entry.get("connections") or [] if str(item).strip()] if isinstance(entry.get("connections"), list) else []
        raw.append({"id": ident, "className": class_name, "tag": tag, "properties": properties, "connections": connections, "path": f"objects[{index}]"})
    drawing = None
    system = "AutoCAD Plant 3D"
    if root:
        drawing = str(root.get("drawing") or root.get("Drawing") or "").strip() or None
        system = str(root.get("sourceSystem") or "AutoCAD Plant 3D")
    return finish(file_name, byte_length, "autocad-json", "Ledger Plant 3D JSON adapter", "Plant 3D JSON extract", drawing, system, raw, warnings)


def load_autocad_csv(file_name, text, byte_length):
    rows = parse_csv(text)
    if not rows:
        return failed_model(file_name, byte_length, "autocad-csv", "The CSV file has no rows.", "Ledger Data Manager CSV adapter")
    header = [cell.strip().lower() for cell in rows[0]]

    def index_of(*names):
        for name in names:
            if name in header:
                return header.index(name)
        return -1

    handle_idx = index_of("handle", "id")
    class_idx = index_of("class", "classname", "class name")
    tag_idx = index_of("tag", "tagname")
    line_idx = index_of("linenumber", "line number", "line")
    conn_idx = index_of("connectedhandles", "connections", "connected to")
    if handle_idx < 0 or class_idx < 0:
        return failed_model(file_name, byte_length, "autocad-csv", "The CSV needs Handle and Class columns.", "Ledger Data Manager CSV adapter")
    warnings = []
    raw = []
    reserved = {index for index in (handle_idx, class_idx, tag_idx, line_idx, conn_idx) if index >= 0}
    for index, row in enumerate(rows[1:]):
        if all(not cell.strip() for cell in row):
            continue
        ident = (row[handle_idx] if handle_idx < len(row) else "").strip()
        if not ident:
            warnings.append({"code": "csv-row", "message": f"Row {index + 2} has no handle and was skipped."})
            continue
        class_name = (row[class_idx] if class_idx < len(row) else "").strip()
        tag_cell = (row[tag_idx] if 0 <= tag_idx < len(row) else "").strip()
        line_cell = (row[line_idx] if 0 <= line_idx < len(row) else "").strip()
        properties = []
        if line_cell:
            properties.append(property_of("LineNumber", line_cell))
        for column, name in enumerate(header):
            if column in reserved or not name:
                continue
            original = rows[0][column] if column < len(rows[0]) else name
            properties.append(property_of(original.strip(), row[column] if column < len(row) else ""))
        connections = []
        if conn_idx >= 0:
            connections = [item.strip() for item in re.split(r"[;|]", row[conn_idx] if conn_idx < len(row) else "") if item.strip()]
        raw.append({
            "id": ident,
            "className": class_name,
            "tag": tag_cell or line_cell or None,
            "properties": properties,
            "connections": connections,
            "path": f"row {index + 2}",
        })
    return finish(
        file_name, byte_length, "autocad-csv", "Ledger Data Manager CSV adapter", "Data Manager CSV",
        None, "AutoCAD Plant 3D Data Manager", raw, warnings,
    )


def parse_csv(text):
    rows = []
    row = []
    cell = []
    quoted = False
    i = 0
    while i < len(text):
        char = text[i]
        if quoted:
            if char == '"':
                if i + 1 < len(text) and text[i + 1] == '"':
                    cell.append('"')
                    i += 2
                    continue
                quoted = False
            else:
                cell.append(char)
            i += 1
            continue
        if char == '"':
            quoted = True
        elif char == ",":
            row.append("".join(cell))
            cell = []
        elif char == "\n":
            row.append("".join(cell))
            rows.append(row)
            row = []
            cell = []
        elif char != "\r":
            cell.append(char)
        i += 1
    if cell or row:
        row.append("".join(cell))
        rows.append(row)
    return [items for items in rows if any(item.strip() for item in items)]
