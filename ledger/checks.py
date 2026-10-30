import re

from ledger.common import display_name, in_check_set

SEVERITY_RANK = {"error": 0, "warning": 1, "review": 2, "info": 3}


def run_checks(model, rules):
    active = [obj for obj in model["objects"] if in_check_set(obj)]
    by_id = {obj["id"]: obj for obj in active}
    findings = []
    counts = {kind: 0 for kind in ("equipment", "piping", "valve", "instrument", "nozzle", "other")}
    for obj in active:
        counts[obj["kind"]] = counts.get(obj["kind"], 0) + 1
    parts = [f"{count} {kind}" for kind, count in counts.items() if count]
    noun = "object" if len(active) == 1 else "objects"
    tail = f" ({', '.join(parts)})" if parts else ""
    findings.append({
        "id": "inventory-count",
        "severity": "info",
        "ruleId": "inventory-count",
        "ruleLabel": "Object count",
        "category": "inventory",
        "projectCheck": False,
        "tag": None,
        "explanation": f"{len(active)} {noun} in the check set{tail}.",
    })

    groups = {}
    for obj in active:
        if not obj.get("tag"):
            continue
        if obj["kind"] not in ("equipment", "valve", "instrument", "piping"):
            continue
        groups.setdefault(f"{obj['kind']}::{obj['tag']}", []).append(obj)
    for group in groups.values():
        if len(group) < 2:
            continue
        ids = ", ".join(obj["id"] for obj in group)
        for obj in group:
            findings.append({
                "id": f"duplicate-tag:{obj['id']}",
                "severity": "error",
                "ruleId": "duplicate-tag",
                "ruleLabel": "Unique tag",
                "category": "identity",
                "projectCheck": False,
                "objectId": obj["id"],
                "tag": obj["tag"],
                "explanation": f"Tag {obj['tag']} is used by {len(group)} {obj['kind']} objects ({ids}). This project treats that tag as unique within the type.",
                "sourceRef": obj["sourcePath"],
            })

    missing = {}
    for edge in model["edges"]:
        for ident in (edge.get("fromId"), edge.get("toId")):
            if not ident or ident in by_id:
                continue
            rec = missing.setdefault(ident, {"peers": [], "path": edge.get("sourcePath")})
            peer = next((item for item in (edge.get("ownerId"), edge.get("fromId"), edge.get("toId")) if item and item != ident and item in by_id), None)
            if peer and peer not in rec["peers"]:
                rec["peers"].append(peer)
    for ident, rec in missing.items():
        peer = by_id.get(rec["peers"][0]) if rec["peers"] else None
        finding = {
            "id": f"broken-reference:{ident}",
            "severity": "error",
            "ruleId": "broken-reference",
            "ruleLabel": "Reference resolves",
            "category": "connection",
            "projectCheck": False,
            "tag": peer["tag"] if peer else None,
            "explanation": f"Connection target {ident} was not imported. It is referenced from {display_name(peer)}." if peer else f"Connection target {ident} was not imported.",
            "sourceRef": rec.get("path"),
        }
        if peer:
            finding["objectId"] = peer["id"]
        findings.append(finding)

    if not model["edges"]:
        findings.append({
            "id": "connections-absent",
            "severity": "info",
            "ruleId": "connections-absent",
            "ruleLabel": "Connections not in import",
            "category": "connection",
            "projectCheck": False,
            "tag": None,
            "explanation": "No connection records were imported. Equipment tie-in and open-end checks were skipped, so a parser gap is not reported as a disconnected object.",
        })
    else:
        segments = [obj for obj in active if obj["objectType"] == "PipingNetworkSegment"]
        hosts = segments or [obj for obj in active if obj["kind"] == "piping"]
        for host in hosts:
            ends = external_ends(host["id"], model)
            if len(ends) >= 2:
                continue
            shown = ", ".join(format_end(ident, by_id) for ident in ends)
            findings.append({
                "id": f"segment-ends:{host['id']}",
                "severity": "review",
                "ruleId": "segment-ends",
                "ruleLabel": "Line ends",
                "category": "connection",
                "projectCheck": False,
                "objectId": host["id"],
                "tag": host["tag"],
                "sourceRef": host["sourcePath"],
                "explanation": (
                    f"{display_name(host)} has no recorded external end. Only explicit connection records are counted, so this is a review item, not a claim that the drawn line is open."
                    if not ends
                    else f"{display_name(host)} has one recorded external end ({shown}). The other end was not in the imported connections."
                ),
            })
        for equipment in [obj for obj in active if obj["kind"] == "equipment"]:
            if equipment_tied(equipment, model):
                continue
            findings.append({
                "id": f"equipment-tiein:{equipment['id']}",
                "severity": "review",
                "ruleId": "equipment-tiein",
                "ruleLabel": "Equipment tie-in",
                "category": "connection",
                "projectCheck": False,
                "objectId": equipment["id"],
                "tag": equipment["tag"],
                "sourceRef": equipment["sourcePath"],
                "explanation": f"No connection to a line or nozzle is recorded for {display_name(equipment)}. Other objects in this file do have connections, so this is worth a designer review rather than a file-wide parser gap.",
            })

    for obj in active:
        mentioned = next((prop for prop in obj["properties"] if prop["name"] == "Text mentions ends" and prop.get("value")), None)
        if not mentioned:
            continue
        findings.append({
            "id": f"text-mentioned-ends:{obj['id']}",
            "severity": "review",
            "ruleId": "text-mentioned-ends",
            "ruleLabel": "Textual ends",
            "category": "connection",
            "projectCheck": False,
            "objectId": obj["id"],
            "tag": obj["tag"],
            "sourceRef": obj["sourcePath"],
            "explanation": f"{display_name(obj)} text mentions {mentioned['value']}. A phrase in the source is not a verified connection, so no tie-in was created.",
        })

    for rule in rules:
        if not rule["enabled"]:
            continue
        for obj in active:
            if obj["kind"] != rule["appliesTo"]:
                continue
            finding = evaluate_field(rule, obj, by_id)
            if finding:
                findings.append(finding)

    findings.sort(key=lambda item: (SEVERITY_RANK[item["severity"]], item["tag"] or "\uffff", item["ruleId"]))
    return findings


def evaluate_field(rule, obj, by_id):
    name = display_name(obj)
    if rule["check"] == "tag":
        if obj.get("tag"):
            return None
        return field_finding(rule, obj, f"Project check: {obj['kind']} {obj['id']} has no tag in the imported data.")
    if rule["check"] == "line-number":
        if obj["objectType"] == "PipingNetworkSegment" and obj.get("parentId"):
            parent = by_id.get(obj["parentId"])
            if parent and parent["objectType"] == "PipingNetworkSystem":
                return None
        if obj.get("tag") or ok_property(obj, r"line.?number"):
            return None
        return field_finding(rule, obj, f"Project check: no line number was imported for {name}.")
    if rule["check"] == "specific-type":
        if obj["kind"] == "valve" and ok_property(obj, r"valve type"):
            return None
        generic = is_generic_valve(obj["objectType"]) if obj["kind"] == "valve" else is_generic_equipment(obj["objectType"])
        if not generic:
            return None
        why = (
            f"Project check: {name} is class “{obj['objectType']}”. A specific type was not imported."
            if obj["objectType"].strip()
            else f"Project check: no class was imported for {name}."
        )
        return field_finding(rule, obj, why)
    if rule["check"] == "instrument-function":
        prop = find_property(obj, r"function|category")
        if prop and prop["status"] == "ok" and (prop.get("value") or "").strip():
            return None
        if prop and prop["status"] == "blank":
            return field_finding(rule, obj, f"Project check: function on {name} is present but blank.")
        if not is_generic_instrument(obj["objectType"]):
            return None
        class_name = obj["objectType"].strip() or "unspecified"
        return field_finding(rule, obj, f"Project check: {name} is class {class_name} and no function was imported.")
    if rule["check"] == "service":
        prop = find_property(obj, r"service")
        if prop and prop["status"] == "ok" and (prop.get("value") or "").strip():
            return None
        if prop and prop["status"] == "blank":
            return field_finding(rule, obj, f"Project check: service on {name} is present but blank.")
        if prop and prop["status"] == "uninterpreted":
            return field_finding(rule, obj, f"Project check: service on {name} could not be interpreted. See import warnings — this is not scored as a blank on the drawing.")
        return field_finding(rule, obj, f"Project check: no service value was imported for {name}.")
    return None


def field_finding(rule, obj, explanation):
    return {
        "id": f"{rule['id']}:{obj['id']}",
        "severity": rule["severity"],
        "ruleId": rule["id"],
        "ruleLabel": rule["label"],
        "category": "field",
        "projectCheck": True,
        "objectId": obj["id"],
        "tag": obj.get("tag"),
        "explanation": explanation,
        "sourceRef": obj["sourcePath"],
    }


def find_property(obj, pattern):
    test = re.compile(pattern, re.I)
    return next((prop for prop in obj["properties"] if test.search(prop["name"]) or test.search(prop.get("label") or "")), None)


def ok_property(obj, pattern):
    prop = find_property(obj, pattern)
    return bool(prop and prop["status"] == "ok" and (prop.get("value") or "").strip())


def is_generic_valve(object_type):
    value = object_type.strip().lower()
    return value in ("", "valve", "pipingcomponent")


def is_generic_equipment(object_type):
    value = object_type.strip().lower()
    return value in ("", "equipment")


def is_generic_instrument(object_type):
    value = object_type.strip().lower()
    return value in ("", "processinstrumentationfunction", "instrument", "instrumentation")


def subtree(root_id, objects):
    ids = {root_id}
    grew = True
    while grew:
        grew = False
        for obj in objects:
            if obj.get("parentId") in ids and obj["id"] not in ids:
                ids.add(obj["id"])
                grew = True
    return ids


def external_ends(root_id, model):
    inside = subtree(root_id, model["objects"])
    ends = []
    for edge in model["edges"]:
        participants = [item for item in (edge.get("ownerId"), edge.get("fromId"), edge.get("toId")) if item]
        if not any(item in inside for item in participants):
            continue
        for item in participants:
            if item not in inside and item not in ends:
                ends.append(item)
    return ends


def equipment_tied(equipment, model):
    ids = subtree(equipment["id"], model["objects"])
    return any(
        any(item and item in ids for item in (edge.get("ownerId"), edge.get("fromId"), edge.get("toId")))
        for edge in model["edges"]
    )


def format_end(ident, by_id):
    obj = by_id.get(ident)
    if not obj:
        return f"{ident} (not imported)"
    return obj["tag"] or obj["id"]
