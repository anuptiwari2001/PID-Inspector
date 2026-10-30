from datetime import datetime, timezone

LEDGER_VERSION = "0.1.0"
KIND_ORDER = ["equipment", "piping", "valve", "instrument", "nozzle", "other"]

LABELS = {
    "TagNameAssignmentClass": "Tag",
    "LineNumberAssignmentClass": "Line number",
    "FluidCodeAssignmentClass": "Fluid code",
    "PipingComponentNumberAssignmentClass": "Component number",
    "ProcessInstrumentationFunctionNumberAssignmentClass": "Instrument number",
    "ProcessInstrumentationFunctionCategoryAssignmentClass": "Function",
    "NominalDiameterNumericalValueRepresentationAssignmentClass": "Nominal diameter",
    "NominalDiameterStandardRepresentationAssignmentClass": "Nominal diameter",
    "ServiceAssignmentClass": "Service",
    "ValveTypeAssignmentClass": "Valve type",
    "FailActionAssignmentClass": "Fail action",
}


def label_for(name: str) -> str:
    if name in LABELS:
        return LABELS[name]
    trimmed = name.replace("AssignmentClass", "").replace("_", " ")
    out = []
    for index, char in enumerate(trimmed):
        if index and char.isupper() and trimmed[index - 1].islower():
            out.append(" ")
        out.append(char)
    text = "".join(out).strip()
    return text or name


def empty_counts():
    return {kind: 0 for kind in KIND_ORDER}


def count_kinds(objects):
    counts = empty_counts()
    for obj in objects:
        counts[obj["kind"]] = counts.get(obj["kind"], 0) + 1
    return counts


def diagnostics_shell(file_name, byte_length, source_kind):
    return {
        "fileRead": True,
        "fileName": file_name,
        "byteLength": byte_length,
        "sourceKind": source_kind,
        "formatLabel": "Unrecognized",
        "formatVersion": None,
        "parserName": "Ledger",
        "parserVersion": LEDGER_VERSION,
        "originatingSystem": None,
        "drawingName": None,
        "discipline": None,
        "objectCount": 0,
        "countsByKind": empty_counts(),
        "skippedTypes": [],
        "uninterpretedProperties": 0,
        "stoppedOnError": False,
        "parseError": None,
        "warnings": [],
        "scopeNotes": [],
        "loadedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def warn(warnings, code, message, detail=None):
    item = {"id": f"{code}-{len(warnings) + 1}", "code": code, "message": message}
    if detail:
        item["detail"] = detail
    warnings.append(item)


def failed_model(file_name, byte_length, source_kind, message, parser_name):
    diagnostics = diagnostics_shell(file_name, byte_length, source_kind)
    diagnostics["parserName"] = parser_name
    diagnostics["stoppedOnError"] = True
    diagnostics["parseError"] = message
    diagnostics["formatLabel"] = "Not loaded"
    warn(diagnostics["warnings"], "parse-stopped", message)
    return blank(diagnostics)


def blank(diagnostics):
    return {
        "diagnostics": diagnostics,
        "objects": [],
        "edges": [],
        "candidates": [],
        "transcript": [],
    }


def display_name(obj):
    return obj["tag"] or obj["id"]


def in_check_set(obj):
    return obj["reviewStatus"] in ("native", "confirmed")
