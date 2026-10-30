# VS Code setup and local models

This is the setup for the `Ledger` folder on your own computer. Inspection runs locally. You do not create an account, and you do not paste a paid API key.

## 1. Install the requirements

Install these before you open the folder.

### Node.js

Install the current **Node.js 22** LTS from [https://nodejs.org](https://nodejs.org). Node 20.19 or newer also works. npm is included.

Check:

```bash
node -v
npm -v
```

### Python

Install **Python 3.10 or newer** from [https://www.python.org/downloads/](https://www.python.org/downloads/).

- Windows: in the installer, enable **Add python.exe to PATH**.
- macOS: `python3` from python.org, or Homebrew `brew install python`.
- Linux: `python3` from your package manager (`sudo apt install python3` on Debian or Ubuntu).

Check:

```bash
python3 --version
```

Windows may only have the `python` command. That is fine:

```powershell
python --version
```

The inspector imports nothing outside the Python standard library. Skip `pip install` unless you later want the VS Code debugger (`debugpy`), which is also free and local.

### VS Code

Install VS Code from [https://code.visualstudio.com](https://code.visualstudio.com).

### What you do not install

- No OpenAI, Anthropic, Google, or xAI key
- No Postgres, unless you later turn on the unused auth scaffold
- No AutoCAD, and no Plant 3D SDK. JSON and CSV extracts are plain files
- No GPU is required for the quality report

## 2. Open the folder

1. Unzip `Ledger.zip`.
2. You should see one folder, `Ledger`, containing `package.json`, `README.md`, `ledger/`, and `src/`.
3. Start VS Code.
4. **File → Open Folder…** and choose `Ledger`.
5. Click **Yes, I trust the authors** if asked.

Opening a parent directory, or a single file, hides the tasks and the Python path. The workspace root must be `Ledger`.

## 3. Extensions

VS Code reads `.vscode/extensions.json`. After the folder opens it should ask to install:

- **Python** (`ms-python.python`) — interpreter, tests, and debug
- **ESLint** (`dbaeumer.vscode-eslint`) — TypeScript lint
- **Tailwind CSS IntelliSense** (`bradlc.vscode-tailwindcss`) — class names in the page

If the prompt does not appear: **View → Extensions**, search `@recommended`, and install the workspace recommendations.

You do not need a Python extension pack beyond that, and you do not need Pylance's paid add-ons. The default Python extension is enough.

### Select the interpreter

1. `Ctrl+Shift+P` (macOS: `Cmd+Shift+P`).
2. Run **Python: Select Interpreter**.
3. Pick the Python 3.10+ you installed. On Windows this is often `Python 3.12`.

`.vscode/settings.json` already points tests at `ledger.test_inspector` and adds the folder to the analysis path.

## 4. Install the page and start it

In the VS Code terminal (**Terminal → New Terminal**):

```bash
npm install
npm run dev
```

Or **Terminal → Run Task…**:

1. `Ledger: install`
2. `Ledger: start app`

Wait until the terminal prints a local URL. Open [http://localhost:8080](http://localhost:8080).

Leave that terminal running. A second terminal is for tests and for the local model.

### If the page opens but a sample fails

The usual cause is that the terminal that started the app cannot find Python.

```bash
# macOS or Linux, from the Ledger folder
export LEDGER_PYTHON=$(which python3)
npm run dev
```

```powershell
# Windows PowerShell, from the Ledger folder
$env:LEDGER_PYTHON = "python"
npm run dev
```

`LEDGER_PYTHON` is only the name of the interpreter on your `PATH`, or a full path to `python.exe`. It is not a key.

### Sign-in

`.grok/app-env.json` sets `VITE_AUTH_ENABLED` to `false`. Do not delete that file. Do not set `DATABASE_URL`. With those two choices the report opens with no login.

If you start Vite yourself (`npx vite`) instead of `npm run dev`, that file is not applied and a sign-in screen can appear. Use `npm run dev`.

## 5. Run the Python tests inside VS Code

**Terminal → Run Task… → Ledger: Python tests**

Or:

```bash
python3 -m unittest ledger.test_inspector
```

Windows:

```powershell
python -m unittest ledger.test_inspector
```

The Testing sidebar can also discover `unittest` because `.vscode/settings.json` enables it. Use the refresh icon on **Testing** if the list is empty, after the interpreter is selected.

### Breakpoints

Optional. From a terminal:

```bash
pip install debugpy
```

Then **Run and Debug** (`Ctrl+Shift+D` / `Cmd+Shift+D`) → **Python: inspector tests** → play. `debugpy` is a local debugger. It does not call a model and it is not required to use Ledger.

## 6. Use the app

1. On the first screen, open **Crude unit** or drop your own file.
2. Read the overview: object counts, import warnings, finding counts.
3. **Inventory** is every object Python kept.
4. **Connections** is the graph of explicit edges. If the file had no connection records, the panel says so instead of drawing a false network.
5. **Findings** is the check list. Open a row for the source path and the explanation.
6. **Rules** switches the process preset and the identity preset, and can turn one rule off. That asks Python to recompute findings.
7. For `feed-sheet.pdf`, the review queue lists candidates. Confirm or reject each one. Nothing from a PDF becomes an object until you confirm it.

Supported drops:

- `.xml` Proteus `PlantModel`, or a DEXPI 2-shaped file (scanned loosely)
- `.json` or `.csv` Plant 3D-style extract
- `.pdf` with a text layer, up to 12 MB

## 7. Local Llama or Qwen, with no paid key

The quality report is finished before any model is involved. Duplicate tags, missing fields, and broken references come from `ledger/checks.py`. A language model must not replace those checks: it will invent tags and call a guess a fact.

Use a local model only as a second pair of eyes on wording you already have, for example “what should I look at on the sheet for this finding?”

[Ollama](https://ollama.com/download) runs the model on your computer. It does not ask for an API key.

### Install Ollama

1. Download the Windows or macOS app from [https://ollama.com/download](https://ollama.com/download), or install the Linux package from that same page.
2. Start the Ollama app, or run `ollama serve`.
3. Pull one model. Pick by memory, not by brand:

| Model | Pull command | Rough memory | When to use it |
| --- | --- | --- | --- |
| Qwen 2.5 3B | `ollama pull qwen2.5:3b` | about 3 GB | laptops with 8 GB RAM |
| Llama 3.2 3B | `ollama pull llama3.2:3b` | about 3 GB | same, if you prefer Llama |
| Qwen 2.5 7B | `ollama pull qwen2.5:7b` | about 6 GB | default in the helper script |
| Llama 3.1 8B | `ollama pull llama3.1` | about 6 GB | alternative 8B-class model |

Larger Qwen or Llama tags exist (`qwen2.5:14b`, `llama3.1:70b`). They are still free and local, but only pull them if the machine has the RAM. No cloud key is involved either way.

Check that it is running:

```bash
ollama list
```

### Ask from VS Code

**Terminal → Run Task… → Ledger: ask local model**, then type the question.

Or from the Ledger folder:

```bash
python3 scripts/ask_local_model.py --model qwen2.5:7b \
  "Finding: valve HV-204 has no specific type, only Valve. What should the designer confirm on the P&ID?"
```

Llama instead of Qwen:

```bash
python3 scripts/ask_local_model.py --model llama3.1 \
  "Finding: line 6-P-1014 has one recorded external end. What does that mean, and what should not be assumed?"
```

Pipe a finding you copied from the report:

```bash
python3 scripts/ask_local_model.py --model qwen2.5:3b <<'EOF'
Tag P-201A is used by 2 equipment objects (eq-1, eq-2).
This project treats that tag as unique within the type.
EOF
```

The script talks only to `http://127.0.0.1:11434`, which is Ollama on this computer. If nothing is listening, it tells you to pull a model. It never falls back to a paid API.

Override the address only if you moved Ollama:

```bash
python3 scripts/ask_local_model.py --host http://127.0.0.1:11434 --model qwen2.5:7b "Explain a missing line number."
```

### What to trust

- Trust the finding list for “this tag is duplicated” or “this reference was not in the file.”
- Treat the model reply as a suggestion about where to look.
- Do not paste a model answer back into the drawing data.
- Do not send a confidential P&ID to a hosted Llama or Qwen API. The helper does not do that. If you use another app that does, that is a different choice, and it is not required here.

### The Ollama HTTP call, if you want it outside the script

This is the whole API the helper uses. It is local. There is no `Authorization` header.

```bash
curl http://127.0.0.1:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5:7b","stream":false,"messages":[{"role":"user","content":"In one sentence, what is a P&ID line number?"}]}'
```

Swap `"model":"llama3.1"` for Llama. The Ledger inspector API is separate and is documented in the README. The page does not call `/api/chat`.

## 8. Call the inspector API yourself

From the Ledger folder, Python reads stdin and writes one JSON object. Details and fields are in the README section **The inspector API**. A short check:

```bash
python3 -m unittest ledger.test_inspector -v
```

A failed import prints a message on stderr and a non-zero exit code. A file Python could open but not fully understand still returns `ok: true`, with the limit written into `model.diagnostics.warnings`. Those warnings are not engineering findings.

## 9. Troubleshooting

| Symptom | What to do |
| --- | --- |
| `python3` not found on Windows | Use `python`, or set `LEDGER_PYTHON` to `python` |
| Port 8080 already in use | Stop the other terminal that ran `npm run dev`, then start it again |
| Blank sign-in wall | Use `npm run dev`, and keep `.grok/app-env.json` with auth set to false |
| `npm install` fails on an optional native module | Use Node 22, delete `node_modules`, run `npm install` again |
| PDF has no candidates | The file is probably a scan without a text layer. Ledger does not OCR |
| DEXPI 2 file looks thin | Expected. The 2.0 reader is a loose scan, not the full exchange schema |
| Ollama model error | `ollama pull` the exact name you passed to `--model` |
| Task `ask local model` does nothing useful | Start the Ollama app first. The quality report still works without it |
