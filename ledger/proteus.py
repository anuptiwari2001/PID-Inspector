import re

from ledger.common import count_kinds, diagnostics_shell, label_for, warn
from ledger.xmlutil import children, local, namespace_of, parse_xml

ALLOWED_FORMATS = {"", "string", "integer", "int", "float", "double", "boolean", "date", "time", "datetime", "anyuri"}
TAG_PROPS = {
    "TagNameAssignmentClass",
    "LineNumberAssignmentClass",
    "PipingComponentNumberAssignmentClass",
    "ProcessInstrumentationFunctionNumberAssignmentClass",
}
KNOWN = {
    "PlantModel", "PlantInformation", "UnitsOfMeasure", "UnitOfMeasure", "Drawing", "MetaData",
    "Equipment", "Nozzle", "PipingNetworkSystem", "PipingNetworkSegment", "PipingComponent",
    "ProcessInstrumentationFunction", "InstrumentationLoopFunction", "ActuatingSystem",
    "ActuatingElectricalSystem", "ActuatingFunction", "MeasuringSystem", "InstrumentComponent",
    "Connection", "GenericAttributes", "GenericAttribute", "CenterLine", "Coordinate", "Presentation",
    "Extent", "Text", "Position", "Scale", "ConnectionPoints", "Node", "Shape", "TrimmedCurve",
    "Circle", "Ellipse", "Line", "PolyLine", "BsplineCurve", "CompositeCurve", "Note", "Label",
    "Association", "PropertyBreak", "PipeConnectorSymbol", "Component", "PlantStructureItem",
    "PersistentID", "Material",
}
FLOW_GRAPHICS = {"SignalLine", "PipeFlowArrow", "InformationFlow"}
PARSER_NAME = "Ledger Proteus loader"


def load_proteus_xml(file_name, text, byte_length):
    diagnostics = diagnostics_shell(file_name, byte_length, "proteus")
    diagnostics["parserName"] = PARSER_NAME
    diagnostics["scopeNotes"] = [
        "Reads equipment, nozzles, piping systems, line segments, piping components, and process instrumentation functions from Proteus XML (DEXPI 1.3 / 1.4).",
        "Relationships come only from Connection elements. Centerlines are not reconstructed into a drawing, and flow arrows are not treated as tie-ins.",
        "This loader is a Python Proteus reader with a narrower scope than a full graphical exchange. It is not pyDEXPI.",
        "DEXPI 2.0.1 is a different serialization and is not parsed as Proteus.",
    ]
    root, message = parse_xml(text)
    if root is None:
        diagnostics["stoppedOnError"] = True
        diagnostics["parseError"] = message
        diagnostics["formatLabel"] = "Proteus XML — not loaded"
        warn(diagnostics["warnings"], "parse-stopped", "Parsing stopped on an error. No engineering checks were run.", message)
        return {"diagnostics": diagnostics, "objects": [], "edges": [], "candidates": [], "transcript": []}
    if local(root.tag) != "PlantModel":
        diagnostics["formatLabel"] = "Not Proteus"
        return {"diagnostics": diagnostics, "objects": [], "edges": [], "candidates": [], "transcript": []}

    namespace = namespace_of(text)
    objects = []
    edges = []
    skipped = {}
    uninterpreted = []
    used_ids = set()
    missing_seq = {"n": 0}
    flow_graphics = {"n": 0}
    drawings = []

    def take_id(raw, element):
        base = (raw or "").strip()
        if not base:
            missing_seq["n"] += 1
            ident = f"missing-id-{element}-{missing_seq['n']}"
            used_ids.add(ident)
            warn(diagnostics["warnings"], "missing-id", f"A {element} element has no ID. It was kept as {ident} so the rest of the file could load.")
            return ident
        if base not in used_ids:
            used_ids.add(base)
            return base
        n = 2
        while f"{base}~{n}" in used_ids:
            n += 1
        ident = f"{base}~{n}"
        used_ids.add(ident)
        warn(diagnostics["warnings"], "duplicate-id", f"ID {base} occurred more than once. The later {element} is kept as {ident}.")
        return ident

    def read_props(node):
        properties = []
        for group in children(node):
            if local(group.tag) != "GenericAttributes":
                continue
            group_set = group.attrib.get("Set")
            for attr in children(group):
                if local(attr.tag) != "GenericAttribute":
                    continue
                name = attr.attrib.get("Name") or attr.attrib.get("name") or "unnamed"
                fmt = attr.attrib.get("Format") or attr.attrib.get("format") or ""
                has_value = "Value" in attr.attrib or "value" in attr.attrib
                raw_value = attr.attrib["Value"] if "Value" in attr.attrib else attr.attrib.get("value")
                prop = {"name": name, "label": label_for(name), "value": raw_value if has_value else None, "status": "ok"}
                if fmt:
                    prop["format"] = fmt
                if group_set:
                    prop["set"] = group_set
                if fmt and fmt.lower() not in ALLOWED_FORMATS:
                    uninterpreted.append(name)
                    prop["status"] = "uninterpreted"
                elif not has_value:
                    uninterpreted.append(name)
                    prop["value"] = None
                    prop["status"] = "uninterpreted"
                else:
                    value = raw_value if raw_value is not None else ""
                    prop["value"] = value
                    prop["status"] = "blank" if value.strip() == "" else "ok"
                properties.append(prop)
        return properties

    def resolve_tag(attrs, properties):
        for key in ("TagName", "Tag"):
            value = (attrs.get(key) or "").strip()
            if value:
                return value
        for prop in properties:
            if prop["status"] == "ok" and (prop.get("value") or "").strip() and prop["name"] in TAG_PROPS:
                return prop["value"].strip()
        return None

    def push_edge(owner_id, attrs, source_path):
        from_id = (attrs.get("FromID") or attrs.get("fromID") or "").strip()
        to_id = (attrs.get("ToID") or attrs.get("toID") or "").strip()
        if not from_id and not to_id:
            warn(diagnostics["warnings"], "connection-empty", "A Connection element has neither FromID nor ToID.", source_path)
            return
        edge = {"id": f"edge-{len(edges) + 1}", "ownerId": owner_id, "fromId": from_id, "toId": to_id, "sourcePath": source_path}
        if attrs.get("FromNode"):
            edge["fromNode"] = attrs["FromNode"]
        if attrs.get("ToNode"):
            edge["toNode"] = attrs["ToNode"]
        edges.append(edge)

    def make_object(node, kind, parent_id, path):
        attrs = node.attrib
        element = local(node.tag)
        properties = read_props(node)
        return {
            "id": take_id(attrs.get("ID") or attrs.get("Id") or attrs.get("id") or "", element),
            "tag": resolve_tag(attrs, properties),
            "kind": kind,
            "objectType": (attrs.get("ComponentClass") or "").strip(),
            "componentName": (attrs.get("ComponentName") or "").strip() or None,
            "properties": properties,
            "connections": [],
            "parentId": parent_id,
            "reviewStatus": "native",
            "confidence": None,
            "page": None,
            "location": None,
            "sourceElement": element,
            "sourcePath": path,
            "drawing": None,
            "hint": None,
        }

    def consume_connections(node, owner_id, path):
        for index, child in enumerate(children(node)):
            if local(child.tag) == "Connection":
                push_edge(owner_id, child.attrib, f"{path}/Connection[{index + 1}]")

    def is_valve(component_class, component_name):
        return re.search(r"valve|check|gate|globe|ball|butterfly|plug|needle|diaphragm", f"{component_class} {component_name or ''}", re.I)

    def extract_component(node, parent_id, path):
        attrs = node.attrib
        kind = "valve" if is_valve(attrs.get("ComponentClass") or "", attrs.get("ComponentName")) else "other"
        obj = make_object(node, kind, parent_id, path)
        objects.append(obj)
        consume_connections(node, obj["id"], path)

    def extract_segment(node, parent_id, path):
        obj = make_object(node, "piping", parent_id, path)
        objects.append(obj)
        consume_connections(node, obj["id"], path)
        for child in children(node):
            if local(child.tag) == "PipingComponent":
                ident = child.attrib.get("ID") or "component"
                extract_component(child, obj["id"], f"{path}/PipingComponent[@ID='{ident}']")

    def extract_equipment(node, path):
        obj = make_object(node, "equipment", None, path)
        objects.append(obj)
        consume_connections(node, obj["id"], path)
        for child in children(node):
            if local(child.tag) != "Nozzle":
                continue
            nozzle_path = f"{path}/Nozzle[@ID='{child.attrib.get('ID') or 'nozzle'}']"
            nozzle = make_object(child, "nozzle", obj["id"], nozzle_path)
            objects.append(nozzle)
            consume_connections(child, nozzle["id"], nozzle_path)

    def extract_system(node, path):
        obj = make_object(node, "piping", None, path)
        objects.append(obj)
        consume_connections(node, obj["id"], path)
        for child in children(node):
            if local(child.tag) != "PipingNetworkSegment":
                continue
            extract_segment(child, obj["id"], f"{path}/PipingNetworkSegment[@ID='{child.attrib.get('ID') or 'segment'}']")

    def extract_instrument(node, parent_id, path):
        obj = make_object(node, "instrument", parent_id, path)
        objects.append(obj)
        consume_connections(node, obj["id"], path)

    def walk(node, parent_id, path):
        tag = local(node.tag)
        if tag not in KNOWN and tag not in FLOW_GRAPHICS:
            skipped[tag] = skipped.get(tag, 0) + 1
            for child in children(node):
                walk(child, parent_id, f"{path}/{tag}")
            return
        if tag in FLOW_GRAPHICS:
            flow_graphics["n"] += 1
            return
        if tag == "PlantInformation":
            attrs = node.attrib
            diagnostics["formatVersion"] = (attrs.get("SchemaVersion") or "").strip() or None
            diagnostics["originatingSystem"] = (attrs.get("OriginatingSystem") or "").strip() or None
            diagnostics["discipline"] = (attrs.get("Discipline") or "").strip() or None
            return
        if tag == "Drawing":
            attrs = node.attrib
            parts = [attrs.get("Name"), attrs.get("Title"), f"rev {attrs['Revision']}" if attrs.get("Revision") else ""]
            label = " · ".join(part.strip() for part in parts if part and part.strip())
            if label:
                drawings.append(label)
            return
        if tag == "Equipment":
            extract_equipment(node, f"{path}/Equipment[@ID='{node.attrib.get('ID') or 'equipment'}']")
            return
        if tag == "PipingNetworkSystem":
            extract_system(node, f"{path}/PipingNetworkSystem[@ID='{node.attrib.get('ID') or 'system'}']")
            return
        if tag == "PipingNetworkSegment":
            extract_segment(node, parent_id, f"{path}/PipingNetworkSegment[@ID='{node.attrib.get('ID') or 'segment'}']")
            return
        if tag == "ProcessInstrumentationFunction":
            extract_instrument(node, parent_id, f"{path}/ProcessInstrumentationFunction[@ID='{node.attrib.get('ID') or 'instrument'}']")
            return
        if tag in {"InstrumentationLoopFunction", "ActuatingSystem", "MeasuringSystem"}:
            for child in children(node):
                walk(child, parent_id, f"{path}/{tag}")
            return
        for child in children(node):
            walk(child, parent_id, path)

    for child in children(root):
        walk(child, None, "/PlantModel")

    version = diagnostics["formatVersion"]
    if not version:
        warn(diagnostics["warnings"], "schema-missing", "PlantInformation has no SchemaVersion. Proteus interpretation was still attempted.")
        diagnostics["formatLabel"] = "Proteus XML (version not stated)"
    else:
        major = version.split(".")[0]
        diagnostics["formatLabel"] = f"Proteus Schema {version}"
        if not major.isdigit() or int(major) < 3 or int(major) > 4:
            warn(
                diagnostics["warnings"],
                "schema-unsupported",
                f"Schema version {version} is outside Proteus 3.x–4.x, which is what this loader supports for DEXPI 1.3/1.4.",
                "Objects were still read. Treat missing data as an import limit unless you know this schema.",
            )
    if namespace:
        diagnostics["scopeNotes"] = [f"XML namespace: {namespace}", *diagnostics["scopeNotes"]]

    unique = list(dict.fromkeys(drawings))
    diagnostics["drawingName"] = unique[0] if unique else None
    if len(unique) > 1:
        diagnostics["drawingName"] = "; ".join(unique)
        warn(diagnostics["warnings"], "multi-drawing", f"This file contains {len(unique)} drawing labels. Ledger reports them as one model.", "; ".join(unique))

    if flow_graphics["n"]:
        count = flow_graphics["n"]
        warn(
            diagnostics["warnings"],
            "graphic-connectivity",
            f"{count} signal line or flow arrow element{'' if count == 1 else 's'} stayed graphical and were not turned into connections.",
            "That is a parser limit. Do not read it as an open line on the sheet.",
        )
    if uninterpreted:
        diagnostics["uninterpretedProperties"] = len(uninterpreted)
        warn(
            diagnostics["warnings"],
            "property-uninterpreted",
            f"{len(uninterpreted)} propert{'y' if len(uninterpreted) == 1 else 'ies'} could not be interpreted.",
            ", ".join(uninterpreted),
        )
    if skipped:
        diagnostics["skippedTypes"] = [{"name": name, "count": count} for name, count in sorted(skipped.items(), key=lambda item: -item[1])]
        listed = ", ".join(f"{item['name']} ({item['count']})" for item in diagnostics["skippedTypes"])
        count = len(diagnostics["skippedTypes"])
        warn(
            diagnostics["warnings"],
            "type-skipped",
            f"{count} element type{'' if count == 1 else 's'} {'is' if count == 1 else 'are'} not interpreted by this loader.",
            listed,
        )

    by_id = {obj["id"]: obj for obj in objects}
    for edge in edges:
        participants = []
        for ident in (edge["ownerId"], edge["fromId"], edge["toId"]):
            if ident and ident not in participants:
                participants.append(ident)
        for ident in participants:
            obj = by_id.get(ident)
            if not obj:
                continue
            for other in participants:
                if other == ident or any(link["targetId"] == other for link in obj["connections"]):
                    continue
                target = by_id.get(other)
                obj["connections"].append({
                    "targetId": other,
                    "targetTag": target["tag"] if target else None,
                    "relation": "connects-to",
                })
    for obj in objects:
        if obj["kind"] != "nozzle" or not obj["parentId"]:
            continue
        parent = by_id.get(obj["parentId"])
        if not parent:
            continue
        for link in obj["connections"]:
            if link["targetId"] == parent["id"] or any(item["targetId"] == link["targetId"] for item in parent["connections"]):
                continue
            parent["connections"].append({**link, "relation": "via-nozzle"})
    for obj in objects:
        obj["drawing"] = diagnostics["drawingName"]
    diagnostics["objectCount"] = len(objects)
    diagnostics["countsByKind"] = count_kinds(objects)
    return {"diagnostics": diagnostics, "objects": objects, "edges": edges, "candidates": [], "transcript": []}
