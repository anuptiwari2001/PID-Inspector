def with_candidate_status(model, ident, status):
    candidates = [{**item, "status": status} if item["id"] == ident else dict(item) for item in model["candidates"]]
    candidate = next((item for item in candidates if item["id"] == ident), None)
    objects = [obj for obj in model["objects"] if obj["id"] != ident]
    if candidate and status == "confirmed":
        objects.append(candidate_to_object(candidate, model))
    return {**model, "candidates": candidates, "objects": objects}


def confirm_high_confidence(model, threshold=0.85):
    next_model = model
    for candidate in model["candidates"]:
        if candidate["status"] == "unreviewed" and candidate["confidence"] >= threshold:
            next_model = with_candidate_status(next_model, candidate["id"], "confirmed")
    return next_model


def candidate_to_object(candidate, model):
    properties = [{"name": "Extracted text", "label": "Extracted text", "value": candidate["context"], "status": "ok"}]
    if candidate.get("service"):
        properties.insert(0, {"name": "Service", "label": "Service", "value": candidate["service"], "status": "ok"})
    if candidate.get("functionName"):
        properties.insert(0, {"name": "Function", "label": "Function", "value": candidate["functionName"], "status": "ok"})
    if candidate.get("mentionedEnds"):
        properties.append({"name": "Text mentions ends", "label": "Text mentions ends", "value": candidate["mentionedEnds"], "status": "ok"})
    return {
        "id": candidate["id"],
        "tag": candidate["suggestedTag"],
        "kind": candidate["suggestedKind"],
        "objectType": candidate["suggestedType"],
        "componentName": None,
        "properties": properties,
        "connections": [],
        "parentId": None,
        "reviewStatus": "confirmed",
        "confidence": candidate["confidence"],
        "page": candidate["page"],
        "location": candidate["location"],
        "sourceElement": "PdfText",
        "sourcePath": candidate["location"],
        "drawing": model["diagnostics"].get("drawingName"),
        "hint": candidate.get("hint"),
    }
