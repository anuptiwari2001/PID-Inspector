<<<<<<< HEAD
# Ledger

Ledger is a one-drawing P&ID quality report. You open a structured drawing file, or a PDF text layer, and it lists the tags, the connections it could read, and the checks that failed.

The page is a React app. The inspector itself is Python, in the `ledger/` folder. The page does not reimplement the checks. It sends the file to Python and shows the report Python returns.

No account, database, or paid API key is required. Quality checks are deterministic rules. A local Llama or Qwen model is optional, and only if you want a plain-language note about a finding. That model stays on your machine. See [docs/VSCODE.md](docs/VSCODE.md).

## What you need

| Tool | Version | Required for |
| --- | --- | --- |
| Node.js | 20.19+ or 22 | the page (`npm run dev`) |
| npm | comes with Node | installing the page |
| Python | 3.10 or newer | reading files and running checks |
| VS Code | current | editing and running tasks |
| Ollama | any recent build | optional local Llama / Qwen only |

Python uses the standard library only. Do not `pip install` anything to run the inspector. Do not set `OPENAI_API_KEY`, `XAI_API_KEY`, or any other model key.

Sign-in is off when `.grok/app-env.json` contains `"VITE_AUTH_ENABLED": "false"`. That file is already in this folder. Leave `DATABASE_URL` unset.

## Open it in VS Code

1. Unzip so you have one folder named `Ledger`.
2. In VS Code choose **File → Open Folder** and select that folder. Do not open a parent folder.
3. If VS Code asks you to trust the folder, trust it.
4. When it offers recommended extensions, install them. They are Python, ESLint, and Tailwind.
5. Open a terminal in VS Code (**Terminal → New Terminal**) and run:

```bash
node -v
python3 --version
npm install
npm run dev
```

On Windows, if `python3` is not found, use `python --version`. The app looks for `python3` first and then `python`. To force one interpreter:

```bash
# macOS / Linux
export LEDGER_PYTHON=python3

# Windows PowerShell
$env:LEDGER_PYTHON = "python"
```

6. Open [http://localhost:8080](http://localhost:8080).

You can also use **Terminal → Run Task** and pick `Ledger: install`, then `Ledger: start app`.

The full click-by-click guide, including the local model, is in [docs/VSCODE.md](docs/VSCODE.md).

## How a report is produced

```text
file drop or sample
        |
        v
React page  --JSON-->  Python package `ledger`
                          |  pick a reader from the file type
                          |  build one normalized model
                          |  run the same checks for every source
                          v
                       model + findings
        |
        v
inventory, connections, findings, detail
```

Readers stay separate from the checks. A new file type only needs a new reader. It does not need new rules.

One file is one drawing. Ledger does not merge a project.

### What each reader will and will not do

| File | Reader | What you get |
| --- | --- | --- |
| Proteus XML (`PlantModel`, DEXPI 1.3 style) | `ledger/proteus.py` | Equipment, piping, valves, instruments, nozzles, and connections that are explicit in the XML |
| DEXPI 2 XML | `ledger/loose.py` | A scan of tagged elements. This is not a full DEXPI 2.0.1 parser |
| Plant 3D JSON or CSV extract | `ledger/autocad.py` | Rows or objects you already exported. There is no live AutoCAD SDK in this app |
| PDF | `ledger/pdftext.py` | Tag-like strings from the text layer, as candidates a designer confirms. A scanned drawing with no text layer stays empty |

A PDF is a page description, not a DEXPI file. Confirming a candidate adds it to the model. Rejecting it leaves it out. High-confidence candidates can be confirmed together from the review queue.

### Checks

These always run when the data is present:

- unique tag inside equipment, valve, instrument, and piping
- a connection target that was not imported
- a piping segment with fewer than two recorded external ends (review, not a claim the line is drawn open)
- equipment with no recorded tie-in, only when the file has other connections
- a phrase in text that mentions ends, which is not turned into a connection

Project field rules (process preset, on by default):

- equipment tag, specific class, and service
- valve tag, specific type, and service
- line number
- instrument tag and function

The identity preset keeps tag and line-number rules only. Reference and connection reviews still run. Toggles in the rules panel call Python again. They do not invent a second copy of the rules in the browser.

Import warnings are parser limits. They are not the same thing as a failed engineering check.

## Samples

Files in `public/samples/`:

- `crude-unit.proteus.xml` — messy Proteus sheet, expected findings
- `cooling-water.proteus.xml` — smaller Proteus sheet
- `dexpi-2-stub.xml` — DEXPI 2-shaped stub, scanned loosely
- `plant3d-export.json` and `plant3d-datamanager.csv` — Plant 3D-style extracts
- `feed-sheet.pdf` — text-layer candidates for the review queue

## The inspector API

The page never imports the Python files into the browser. A server function posts one JSON object to a Python process:

```text
python3 -m ledger
```

The process reads one JSON document from stdin and writes one JSON document to stdout. Working directory must be this folder, so Python can import `ledger`.

There are four operations. Every successful response has the same shape.

### Request

| Field | Used by | Meaning |
| --- | --- | --- |
| `op` | all | `inspect`, `checks`, `candidate`, or `confirm-high` |
| `fileName` | `inspect` | Original file name. The extension helps pick a reader |
| `dataBase64` | `inspect` | Raw file bytes, base64 |
| `model` | `checks`, `candidate`, `confirm-high` | The model returned by an earlier call |
| `ruleSetId` | all | `process` (default) or `identity` |
| `overrides` | all | Map of rule id → `{ "enabled": bool, "severity": "error" \| "warning" \| "review" \| "info" }` |
| `candidateId` | `candidate` | Id from `model.candidates` |
| `status` | `candidate` | `unreviewed`, `confirmed`, or `rejected` |

### Response

```json
{
  "ok": true,
  "model": {},
  "findings": []
}
```

`ok: false` includes `message` and no report. The model is the normalized drawing:

- `diagnostics` — file name, source kind, parser name, counts, import warnings
- `objects` — tags, kind, properties, review status, source path
- `edges` — connections that were explicit in the source
- `candidates` — PDF strings that are not objects until a designer confirms them

A finding has `severity` (`error`, `warning`, `review`, `info`), `ruleId`, `ruleLabel`, `explanation`, and usually `tag` plus `objectId`.

### Call it from a terminal

```bash
python3 - <<'PY'
import base64, json, subprocess
raw = open("public/samples/crude-unit.proteus.xml", "rb").read()
payload = {
    "op": "inspect",
    "fileName": "crude-unit.proteus.xml",
    "dataBase64": base64.b64encode(raw).decode(),
    "ruleSetId": "process",
    "overrides": {},
}
proc = subprocess.run(["python3", "-m", "ledger"], input=json.dumps(payload), text=True, capture_output=True, check=True)
report = json.loads(proc.stdout)
print(report["ok"], len(report["findings"]), "findings")
for item in report["findings"][:8]:
    print(item["severity"], item["ruleLabel"], item.get("tag") or "")
PY
```

On Windows, run that with `python` if `python3` is not on `PATH`.

### Where the page calls it

| Page action | `op` |
| --- | --- |
| Drop a file, or open a sample | `inspect` |
| Change a rule or its severity | `checks` |
| Confirm or reject one PDF candidate | `candidate` |
| Confirm every high-confidence candidate | `confirm-high` |

The browser entry is `ledgerOp` in `src/lib/inspector/engine.ts`. `src/lib/inspector/python.server.ts` starts the process. `src/lib/inspector/client.ts` is what the panels call.

## Tests

```bash
python3 -m unittest ledger.test_inspector
```

In VS Code: **Terminal → Run Task → Ledger: Python tests**. To step through a test, install the free debugger once (`pip install debugpy`) and use **Run and Debug → Python: inspector tests**. The running app does not need `debugpy`.

## Local Llama or Qwen

The checks do not call a language model. If you want a short explanation of a finding, use Ollama on your own machine. It is free. There is no key to paste.

```bash
ollama pull qwen2.5:7b
python3 scripts/ask_local_model.py "Finding: tag P-101 is used by 2 equipment objects. What should the designer check on the drawing?"
```

Other local names that work the same way: `qwen2.5:3b` (smaller), `llama3.1`, `llama3.2:3b`. Pass `--model llama3.1` to switch. Setup, RAM, and what the model must not be trusted to do are in [docs/VSCODE.md](docs/VSCODE.md).

## Layout

```text
ledger/                 Python inspector (the source of the checks)
  __main__.py           stdin JSON → stdout JSON
  load.py               chooses a reader
  proteus.py            Proteus / DEXPI 1.3 XML
  loose.py              loose XML, including a DEXPI 2 stub
  autocad.py            Plant 3D JSON and CSV extracts
  pdftext.py            PDF text-layer candidates
  checks.py             findings
  rules.py              process and identity presets
public/samples/         drawings you can open from the page
src/                    React report UI
scripts/ask_local_model.py
docs/VSCODE.md          VS Code and local-model guide
```
=======
# PID-Inspector
A local P&amp;ID quality inspector. It reads Proteus XML, a Plant 3D JSON or CSV extract, or a PDF text layer, then lists tags, connections, and findings. No paid API key. Anyone can customize it by tag and use it.
>>>>>>> a10f60d5cb3578a9955f8c9a5597aa69452d4165
