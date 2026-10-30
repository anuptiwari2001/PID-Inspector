PROCESS_RULES = [
    {"id": "eq-tag", "label": "Equipment tag", "detail": "Equipment must have a tag.", "appliesTo": "equipment", "check": "tag", "severity": "error", "enabled": True},
    {"id": "eq-type", "label": "Equipment type", "detail": "Equipment must have a specific class, not a generic Equipment element.", "appliesTo": "equipment", "check": "specific-type", "severity": "error", "enabled": True},
    {"id": "eq-service", "label": "Equipment service", "detail": "Equipment must have a service value.", "appliesTo": "equipment", "check": "service", "severity": "warning", "enabled": True},
    {"id": "valve-tag", "label": "Valve tag", "detail": "A valve must have a tag.", "appliesTo": "valve", "check": "tag", "severity": "error", "enabled": True},
    {"id": "valve-type", "label": "Valve type", "detail": "A valve must have a specific type, not only Valve.", "appliesTo": "valve", "check": "specific-type", "severity": "warning", "enabled": True},
    {"id": "valve-service", "label": "Valve service", "detail": "A valve must have a service value.", "appliesTo": "valve", "check": "service", "severity": "warning", "enabled": True},
    {"id": "line-number", "label": "Line number", "detail": "A line must have a line number. Segments inherit it from their piping system.", "appliesTo": "piping", "check": "line-number", "severity": "error", "enabled": True},
    {"id": "inst-tag", "label": "Instrument tag", "detail": "An instrument must have a tag.", "appliesTo": "instrument", "check": "tag", "severity": "error", "enabled": True},
    {"id": "inst-function", "label": "Instrument function", "detail": "An instrument must have a function, or a specific class that already states it.", "appliesTo": "instrument", "check": "instrument-function", "severity": "warning", "enabled": True},
]

RULE_SETS = [
    {
        "id": "process",
        "name": "Process project standard",
        "description": "Tags, classes, line numbers, valve type, instrument function, and service. These are project checks, not universal DEXPI rules.",
        "rules": PROCESS_RULES,
    },
    {
        "id": "identity",
        "name": "Identity only",
        "description": "Tags and line numbers only. Reference errors and connection reviews still run.",
        "rules": [{**rule, "enabled": rule["id"] in {"eq-tag", "valve-tag", "line-number", "inst-tag"}} for rule in PROCESS_RULES],
    },
]


def effective_rules(rule_set_id, overrides):
    chosen = next((item for item in RULE_SETS if item["id"] == rule_set_id), RULE_SETS[0])
    rules = []
    for rule in chosen["rules"]:
        override = (overrides or {}).get(rule["id"]) or {}
        rules.append({
            **rule,
            "enabled": override.get("enabled", rule["enabled"]),
            "severity": override.get("severity", rule["severity"]),
        })
    return rules
