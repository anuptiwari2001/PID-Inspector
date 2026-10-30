import re
import zlib

from ledger.common import count_kinds, diagnostics_shell, warn

NOT_EQUIPMENT = {"PID", "DWG", "ISO", "REV", "SH", "NOTE"}

BUBBLE_KIND = {
    "ESDV": "valve", "SDV": "valve", "XV": "valve", "HV": "valve", "FV": "valve", "LV": "valve",
    "PV": "valve", "TV": "valve", "BV": "valve", "GV": "valve", "CV": "valve", "PSV": "valve",
    "PRV": "valve", "RV": "valve", "MOV": "valve", "HCV": "valve", "PCV": "valve", "FCV": "valve",
    "LCV": "valve", "TCV": "valve", "BDV": "valve",
    "PDIT": "instrument", "PDT": "instrument", "PDI": "instrument", "PIT": "instrument",
    "FIT": "instrument", "LIT": "instrument", "TIT": "instrument", "AIT": "instrument",
    "PIC": "instrument", "FIC": "instrument", "LIC": "instrument", "TIC": "instrument",
    "HIC": "instrument", "PT": "instrument", "FT": "instrument", "LT": "instrument",
    "TT": "instrument", "AT": "instrument", "PI": "instrument", "FI": "instrument",
    "LI": "instrument", "TI": "instrument", "PG": "instrument", "TG": "instrument",
    "LG": "instrument", "FE": "instrument", "LE": "instrument", "TE": "instrument",
    "PE": "instrument", "AE": "instrument",
}


def load_pdf(file_name, data: bytes):
    diagnostics = diagnostics_shell(file_name, len(data), "pdf")
    diagnostics["parserName"] = "Ledger PDF text layer"
    header = data[:16].decode("latin-1", "replace")
    version = re.search(r"%PDF-(\d+\.\d+)", header)
    diagnostics["formatVersion"] = version.group(1) if version else None
    diagnostics["formatLabel"] = f"PDF {version.group(1)} (text layer)" if version else "PDF (text layer)"
    diagnostics["scopeNotes"] = [
        "A PDF is a page description. It does not contain DEXPI objects.",
        "Text-layer tags are candidates until a designer confirms them. Recognition confidence is not engineering correctness.",
        "No symbol recognition and no OCR. A scanned sheet with no text layer produces no candidates.",
        "Phrases such as “from P-101 to V-201” are kept as text. They are not created as connections.",
    ]
    warn(
        diagnostics["warnings"],
        "pdf-not-dexpi",
        "This PDF was not read as a DEXPI model. Extracted tags stay unreviewed until you confirm them.",
        "Confirming a candidate adds it to the check set. It does not prove the symbol on the sheet.",
    )
    extracted = extract_lines(data)
    for message in extracted["notes"]:
        warn(diagnostics["warnings"], "pdf-text", message)
    lines = extracted["lines"]
    diagnostics["drawingName"] = drawing_from(lines)
    candidates = candidates_from(lines)
    diagnostics["objectCount"] = 0
    diagnostics["countsByKind"] = count_kinds([])
    if not lines:
        warn(
            diagnostics["warnings"],
            "pdf-no-text",
            "No extractable text layer was found. There are no candidates to review.",
            "Symbol recognition is not part of this inspector.",
        )
    return {
        "diagnostics": diagnostics,
        "objects": [],
        "edges": [],
        "candidates": candidates,
        "transcript": [{"page": line["page"], "text": line["text"]} for line in lines],
    }


def drawing_from(lines):
    for line in lines:
        match = re.search(r"\bPID[-\s]?(\d{2,5}[A-Z]?)\b", line["text"], re.I)
        if match:
            return f"PID-{match.group(1)}"
    return None


def candidates_from(lines):
    found = []
    for line_index, line in enumerate(lines):
        blocked = []

        def take(start, end):
            if any(start < b and end > a for a, b in blocked):
                return False
            blocked.append((start, end))
            return True

        def push(candidate):
            start = candidate.pop("start")
            found.append({
                **candidate,
                "id": f"pdf-{line['page']}-{line_index}-{start}",
                "status": "unreviewed",
                "page": line["page"],
                "context": line["text"],
                "location": (
                    f"page {line['page']}, x {round(line['x'])}, y {round(line['y'])}"
                    if line["x"] or line["y"]
                    else f"page {line['page']}, text item {line_index + 1}"
                ),
            })

        service_match = re.search(r"\bSERVICE\s+(.+)$", line["text"], re.I)
        service = service_match.group(1).strip()[:80] if service_match else None
        from_to = re.search(r"\bFROM\s+([A-Z]{1,4}-?\d{2,5}[A-Z]?)\s+TO\s+([A-Z]{1,4}-?\d{2,5}[A-Z]?)\b", line["text"], re.I)
        mentioned = f"{norm_tag(from_to.group(1))} → {norm_tag(from_to.group(2))}" if from_to else None
        line_re = re.compile(
            r"(?<!\d)(?:"
            r"\d{1,2}(?:-\d{1,2})?(?:/\d{1,2})?\s*(?:\"|”)\s*-\s*[A-Z]{1,6}-\d{3,8}[A-Z]{0,6}(?:-[A-Z0-9().]+)?"
            r"|\d{1,2}\s*-\s*[A-Z]{1,6}\s*-\s*\d{2,5}(?:\s*-\s*[A-Z0-9]+)?"
            r"|\d{2,5}\s*-\s*[A-Z]{1,6}\s*-\s*\d{2,6}(?:\s*-\s*[A-Z0-9]+)?"
            r"|[A-Z]{1,6}-\d{3,8}-[A-Z][A-Z0-9().]*"
            r")",
            re.I,
        )
        for match in line_re.finditer(line["text"]):
            if not take(match.start(), match.end()):
                continue
            tagged = bool(re.search(r"line", line["text"], re.I))
            push({
                "rawText": match.group(0),
                "suggestedTag": norm_tag(match.group(0)),
                "suggestedKind": "piping",
                "suggestedType": "Piping line",
                "confidence": 0.9 if tagged else 0.62,
                "start": match.start(),
                "service": None,
                "mentionedEnds": mentioned,
                "hint": None if tagged else "Line number pattern only. The word “line” was not on this text.",
            })
        valve_re = re.compile(
            r"\b((?:ESDV|SDV|XV|HV|FV|LV|PV|TV|BV|GV|CV|PSV|PRV|RV|MOV|HCV|PCV|FCV|LCV|TCV|BDV)\s*-?\s*\d{2,5}[A-Z]?)\b",
            re.I,
        )
        for match in valve_re.finditer(line["text"]):
            if not take(match.start(), match.end()):
                continue
            specific = valve_type_from_words(line["text"])
            push({
                "rawText": match.group(0),
                "suggestedTag": norm_tag(match.group(0)),
                "suggestedKind": "valve",
                "suggestedType": specific or "Valve",
                "confidence": 0.92 if specific else 0.68,
                "start": match.start(),
                "service": service,
                "hint": None if specific else "The ISA prefix was recognized. A specific valve type was not taken from the prefix alone.",
            })
        inst_re = re.compile(
            r"\b((?:PDIT|PDT|PDI|PIT|FIT|LIT|TIT|AIT|PIC|FIC|LIC|TIC|HIC|PT|FT|LT|TT|AT|PI|FI|LI|TI|PG|TG|LG|FE|LE|TE|PE|AE)\s*-?\s*\d{2,5}[A-Z]?)\b",
            re.I,
        )
        for match in inst_re.finditer(line["text"]):
            if not take(match.start(), match.end()):
                continue
            typed = instrument_from_words(line["text"])
            push({
                "rawText": match.group(0),
                "suggestedTag": norm_tag(match.group(0)),
                "suggestedKind": "instrument",
                "suggestedType": typed["type"] if typed else "Instrument",
                "confidence": 0.92 if typed else 0.68,
                "start": match.start(),
                "functionName": typed["fn"] if typed else None,
                "hint": None if typed else "ISA prefix only. Function was not filled in from the prefix.",
            })
        for match in re.finditer(r"\b([A-Z]{1,4})\s*-\s*(\d{2,5}[A-Z]?)\b", line["text"]):
            if not take(match.start(), match.end()):
                continue
            prefix = match.group(1).upper()
            if prefix in NOT_EQUIPMENT:
                continue
            typed = equipment_from_words(line["text"])
            push({
                "rawText": match.group(0),
                "suggestedTag": norm_tag(match.group(0)),
                "suggestedKind": "equipment",
                "suggestedType": typed or "",
                "confidence": 0.9 if typed else 0.5,
                "start": match.start(),
                "service": service,
                "hint": None if typed else "No equipment class word was found next to this tag.",
            })
        if re.search(r"note|hold", line["text"], re.I):
            for match in re.finditer(r"\b([A-Z]{1,3}-\d{1,5}[A-Z]?)\b", line["text"]):
                if not take(match.start(), match.end()):
                    continue
                push({
                    "rawText": match.group(0),
                    "suggestedTag": norm_tag(match.group(0)),
                    "suggestedKind": "other",
                    "suggestedType": "Unresolved note",
                    "confidence": 0.42,
                    "start": match.start(),
                    "hint": "Found in a note or hold. Class was not assigned.",
                })
    best = {}
    for candidate in found:
        key = f"{candidate['suggestedKind']}:{candidate['suggestedTag']}"
        previous = best.get(key)
        if previous is None or candidate["confidence"] > previous["confidence"]:
            best[key] = candidate
    return list(best.values())


def norm_tag(value):
    return re.sub(r"\s+", "", value).upper()


def valve_type_from_words(line):
    if re.search(r"butterfly", line, re.I):
        return "ButterflyValve"
    if re.search(r"ball", line, re.I):
        return "BallValve"
    if re.search(r"gate", line, re.I):
        return "GateValve"
    if re.search(r"globe", line, re.I):
        return "GlobeValve"
    if re.search(r"check", line, re.I):
        return "CheckValve"
    if re.search(r"control", line, re.I):
        return "ControlValve"
    return None


def instrument_from_words(line):
    fn = None
    if re.search(r"pressure", line, re.I):
        fn = "Pressure"
    elif re.search(r"flow", line, re.I):
        fn = "Flow"
    elif re.search(r"level", line, re.I):
        fn = "Level"
    elif re.search(r"temp", line, re.I):
        fn = "Temperature"
    if not fn:
        return None
    if re.search(r"transmitter", line, re.I):
        return {"type": f"{fn}Transmitter", "fn": fn}
    if re.search(r"gauge", line, re.I):
        return {"type": f"{fn}Gauge", "fn": fn}
    if re.search(r"controller", line, re.I):
        return {"type": f"{fn}Controller", "fn": fn}
    if re.search(r"indicator", line, re.I):
        return {"type": f"{fn}Indicator", "fn": fn}
    return {"type": fn, "fn": fn}


def equipment_from_words(line):
    if re.search(r"centrifugal\s+pump|\bpump\b", line, re.I):
        return "Pump"
    if re.search(r"exchanger|heater|cooler", line, re.I):
        return "HeatExchanger"
    if re.search(r"column|tower", line, re.I):
        return "Column"
    if re.search(r"compressor", line, re.I):
        return "Compressor"
    if re.search(r"tank", line, re.I):
        return "Tank"
    if re.search(r"filter", line, re.I):
        return "Filter"
    if re.search(r"vessel|separator|drum", line, re.I):
        return "Vessel"
    return None


def extract_lines(data: bytes):
    notes = []
    fonts = font_cmaps(data)
    streams = find_streams(data)
    page_count = len(re.findall(r"/Type\s*/Page(?!s)", data.decode("latin-1", "replace")))
    pages = []
    for stream in streams:
        payload = stream["data"]
        if "FlateDecode" in stream["dict"] or payload[:2] in (b"\x78\x9c", b"\x78\x01", b"\x78\xda"):
            try:
                payload = inflate(payload)
            except zlib.error:
                notes.append("One compressed content stream could not be inflated and was skipped.")
                continue
        text = payload.decode("latin-1", "replace")
        if "Tj" not in text and "TJ" not in text:
            continue
        try:
            hits = extract_text_ops(text, fonts)
        except Exception:
            notes.append("One content stream could not be read and was skipped.")
            continue
        if hits:
            pages.append(hits)
    lines = []
    for index, hits in enumerate(pages):
        page = index + 1 if page_count == len(pages) else 1
        for synthetic in bubble_lines(hits):
            lines.append({**synthetic, "page": page})
        groups = {}
        for hit in hits:
            groups.setdefault(round(hit["y"]), []).append(hit)
        for _, group in sorted(groups.items(), key=lambda item: -item[0]):
            group.sort(key=lambda hit: hit["x"])
            parts = [group[0]["text"]]
            for previous, hit in zip(group, group[1:]):
                parts.append(" " if hit["x"] - previous["x"] > 12 else "")
                parts.append(hit["text"])
            text = re.sub(r"\s+", " ", "".join(parts)).strip()
            if not text:
                continue
            lines.append({"page": page, "text": text, "x": group[0]["x"], "y": group[0]["y"]})
    if page_count > 1 and page_count != len(pages):
        notes.append("Page mapping is approximate. More than one page was found, but content streams did not line up one-to-one.")
    if not lines and fonts:
        notes.append("Text was stored as font codes, and none of it decoded to letters.")
    return {"lines": lines, "notes": notes}


def bubble_lines(hits):
    """Join a symbol prefix and a nearby number that AutoCAD drew as two text runs."""
    prefixes = []
    numbers = []
    for hit in hits:
        text = hit["text"].strip()
        if text in BUBBLE_KIND:
            prefixes.append(hit)
        elif re.fullmatch(r"\d{2,5}[A-Z]?", text):
            numbers.append(hit)
    used = set()
    synthetic = []
    for prefix in prefixes:
        best = None
        best_distance = 220
        for number in numbers:
            if id(number) in used:
                continue
            distance = ((number["x"] - prefix["x"]) ** 2 + (number["y"] - prefix["y"]) ** 2) ** 0.5
            if distance < best_distance:
                best_distance = distance
                best = number
        if best is None:
            continue
        used.add(id(best))
        synthetic.append({
            "text": f"{prefix['text'].strip()}-{best['text'].strip()}",
            "x": prefix["x"],
            "y": prefix["y"],
        })
    return synthetic


def find_streams(data: bytes):
    streams = []
    index = 0
    while True:
        found = data.find(b"stream", index)
        if found < 0:
            break
        # "endstream" contains the letters "stream". A real token is preceded by whitespace.
        if found == 0 or data[found - 1:found] not in (b"\n", b"\r", b" ", b"\t"):
            index = found + 6
            continue
        start = found + 6
        if data[start:start + 2] == b"\r\n":
            start += 2
        elif data[start:start + 1] in (b"\n", b"\r"):
            start += 1
        end = data.find(b"endstream", start)
        if end < 0:
            break
        chunk = data[start:end]
        if chunk.endswith(b"\r\n"):
            chunk = chunk[:-2]
        elif chunk.endswith(b"\n") or chunk.endswith(b"\r"):
            chunk = chunk[:-1]
        window = data[max(0, found - 500):found].decode("latin-1", "replace")
        streams.append({"dict": window, "data": chunk})
        index = end + 9
    return streams


def font_cmaps(data: bytes):
    text = data.decode("latin-1", "replace")
    cmaps = {}
    font_objects = {}
    for match in re.finditer(r"(?m)^(\d+)\s+0\s+obj\b(.*?)endobj", text, re.S):
        body = match.group(2)
        obj = int(match.group(1))
        if "beginbfchar" in body or "beginbfrange" in body:
            cmaps[obj] = parse_cmap(body)
        unicode_ref = re.search(r"/ToUnicode\s+(\d+)\s+0\s+R", body)
        if unicode_ref and re.search(r"/Type\s*/Font\b", body):
            font_objects[obj] = int(unicode_ref.group(1))
    names = {}
    for block in re.findall(r"/Font\s*<<(.*?)>>", text, re.S):
        for name, obj in re.findall(r"/([A-Za-z0-9]+)\s+(\d+)\s+0\s+R", block):
            names[name] = int(obj)
    decoded = {}
    for name, obj in names.items():
        cmap = cmaps.get(font_objects.get(obj))
        if cmap:
            decoded[name] = cmap
    return decoded


def parse_cmap(text):
    mapping = {}
    for block in re.findall(r"beginbfchar(.*?)endbfchar", text, re.S):
        for src, dst in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block):
            mapping[int(src, 16)] = unicode_from_hex(dst)
    for block in re.findall(r"beginbfrange(.*?)endbfrange", text, re.S):
        for match in re.finditer(
            r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*(?:<([0-9A-Fa-f]+)>|\[([^\]]*)\])",
            block,
        ):
            start = int(match.group(1), 16)
            end = int(match.group(2), 16)
            if match.group(3):
                dest = int(match.group(3), 16)
                for offset, code in enumerate(range(start, end + 1)):
                    mapping[code] = chr(dest + offset)
            else:
                dests = re.findall(r"<([0-9A-Fa-f]+)>", match.group(4) or "")
                for code, dest in zip(range(start, end + 1), dests):
                    mapping[code] = unicode_from_hex(dest)
    return mapping


def unicode_from_hex(value):
    raw = bytes.fromhex(value)
    if len(raw) <= 1:
        return chr(raw[0]) if raw else ""
    return raw.decode("utf-16-be", "replace").replace("\ufffd", "")


def decode_hex_text(body, cmap, fonts):
    codes = hex_codes(body)
    if not codes:
        return ""

    def apply(table):
        if not table:
            return None
        chars = []
        for code in codes:
            if code not in table:
                return None
            chars.append(table[code])
        return "".join(chars)

    text = apply(cmap)
    if text is not None:
        return text
    for table in fonts.values():
        text = apply(table)
        if text is not None:
            return text
    raw = bytes.fromhex(re.sub(r"\s+", "", body))
    if raw and all(byte < 128 for byte in raw):
        return raw.decode("ascii", "replace")
    return ""


def hex_codes(body):
    compact = re.sub(r"\s+", "", body)
    if not compact or len(compact) % 2:
        return []
    width = 4 if len(compact) % 4 == 0 else 2
    return [int(compact[index:index + width], 16) for index in range(0, len(compact), width)]


def inflate(data: bytes) -> bytes:
    try:
        return zlib.decompress(data)
    except zlib.error:
        raw = data[2:-4] if len(data) > 6 else data
        return zlib.decompress(raw, -15)


def extract_text_ops(content: str, fonts=None):
    hits = []
    fonts = fonts or {}
    i = 0
    x = 0.0
    y = 0.0
    leading = 14.0
    length = len(content)
    current_font = None
    pending_name = None
    while i < length:
        char = content[i]
        if char == "%":
            while i < length and content[i] != "\n":
                i += 1
            continue
        if char in " \n\r\t":
            i += 1
            continue
        if content.startswith("T*", i):
            y -= leading
            i += 2
            continue
        if char == "(":
            parsed = read_pdf_string(content, i)
            i = parsed["next"]
            k = i
            while k < length and content[k].isspace():
                k += 1
            if content.startswith("Tj", k):
                hits.append({"text": parsed["value"], "x": x, "y": y})
                i = k + 2
            elif k < length and content[k] == "'":
                y -= leading
                hits.append({"text": parsed["value"], "x": x, "y": y})
                i = k + 1
            continue
        if char == "[":
            parts = []
            i += 1
            while i < length and content[i] != "]":
                if content[i] == "(":
                    parsed = read_pdf_string(content, i)
                    parts.append(parsed["value"])
                    i = parsed["next"]
                else:
                    i += 1
            if i < length and content[i] == "]":
                i += 1
            k = i
            while k < length and content[k].isspace():
                k += 1
            if content.startswith("TJ", k):
                text = "".join(parts)
                if text.strip():
                    hits.append({"text": text, "x": x, "y": y})
                i = k + 2
            continue
        number = re.match(r"[+-]?(?:\d+\.?\d*|\.\d+)", content[i:])
        if number:
            nums = [float(number.group(0))]
            i += number.end()
            while i < length:
                k = i
                while k < length and content[k].isspace():
                    k += 1
                more = re.match(r"[+-]?(?:\d+\.?\d*|\.\d+)", content[k:]) if k < length else None
                if not more:
                    i = k
                    break
                nums.append(float(more.group(0)))
                i = k + more.end()
            while i < length and content[i].isspace():
                i += 1
            if content.startswith("Td", i) or content.startswith("TD", i):
                x += nums[-2] if len(nums) >= 2 else 0
                y += nums[-1] if nums else 0
                i += 2
                continue
            if content.startswith("Tm", i):
                x = nums[-2] if len(nums) >= 2 else x
                y = nums[-1] if nums else y
                i += 2
                continue
            if content.startswith("TL", i):
                leading = nums[-1] if nums else leading
                i += 2
                continue
            if content.startswith("Tf", i):
                if pending_name:
                    current_font = pending_name
                i += 2
                continue
            continue
        if char == "<":
            if content.startswith("<<", i):
                i += 2
                continue
            end = content.find(">", i + 1)
            if end < 0:
                i += 1
                continue
            decoded = decode_hex_text(content[i + 1:end], fonts.get(current_font) or {}, fonts)
            i = end + 1
            k = i
            while k < length and content[k].isspace():
                k += 1
            if content.startswith("Tj", k) and decoded.strip():
                hits.append({"text": decoded, "x": x, "y": y})
                i = k + 2
            continue
        if char == "/":
            i += 1
            start = i
            while i < length and re.match(r"[A-Za-z0-9_.]", content[i]):
                i += 1
            pending_name = content[start:i]
            continue
        i += 1
    return hits


def read_pdf_string(source, index):
    value = []
    i = index + 1
    while i < len(source):
        char = source[i]
        if char == "\\":
            if i + 1 >= len(source):
                break
            nxt = source[i + 1]
            if nxt == "n":
                value.append("\n")
            elif nxt == "r":
                value.append("\r")
            elif nxt == "t":
                value.append("\t")
            elif nxt in "()\\":
                value.append(nxt)
            elif "0" <= nxt <= "7":
                octal = nxt
                j = i + 2
                for _ in range(2):
                    if j < len(source) and "0" <= source[j] <= "7":
                        octal += source[j]
                        j += 1
                    else:
                        break
                value.append(chr(int(octal, 8)))
                i = j
                continue
            elif nxt in "\n\r":
                i += 2
                if nxt == "\r" and i < len(source) and source[i] == "\n":
                    i += 1
                continue
            else:
                value.append(nxt)
            i += 2
            continue
        if char == ")":
            return {"value": "".join(value), "next": i + 1}
        value.append(char)
        i += 1
    return {"value": "".join(value), "next": i}
