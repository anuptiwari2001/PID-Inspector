import base64

from ledger.candidates import confirm_high_confidence, with_candidate_status
from ledger.checks import run_checks
from ledger.load import inspect_bytes
from ledger.rules import effective_rules


def dispatch(payload):
    op = payload.get("op")
    rule_set = payload.get("ruleSetId") or "process"
    overrides = payload.get("overrides") or {}
    if op == "inspect":
        raw = base64.b64decode(payload.get("dataBase64") or "")
        model = inspect_bytes(payload.get("fileName") or "drawing", raw)
    elif op == "candidate":
        model = with_candidate_status(payload["model"], payload["candidateId"], payload["status"])
    elif op == "confirm-high":
        model = confirm_high_confidence(payload["model"])
    elif op == "checks":
        model = payload["model"]
    else:
        return {"ok": False, "message": "Unknown inspection request."}
    rules = effective_rules(rule_set, overrides)
    return {"ok": True, "model": model, "findings": run_checks(model, rules)}
