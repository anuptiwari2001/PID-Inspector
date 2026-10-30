import { useRef, useState } from "react";
import { SAMPLES } from "@/lib/inspector/samples";
import { useInspector } from "@/lib/inspector/store";
import { inspectNamed } from "@/lib/inspector/client";
import { Meta } from "./ui";

const STEPS = [
  ["Read", "Proteus XML, a PDF text layer, or a Plant 3D extract."],
  ["Normalize", "One object record, whichever source it came from."],
  ["Check", "Project rules, kept apart from import warnings."],
  ["Report", "Inventory, connections, and findings you can search."],
];

export function Intake() {
  const loading = useInspector((state) => state.loading);
  const loadError = useInspector((state) => state.loadError);
  const inputRef = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);

  async function takeFile(file: File | undefined) {
    if (!file) return;
    const bytes = new Uint8Array(await file.arrayBuffer());
    await inspectNamed(file.name, bytes);
  }

  async function takeSample(file: string) {
    const store = useInspector.getState();
    store.setLoading(true);
    store.setLoadError(null);
    try {
      const response = await fetch(`/samples/${file}`);
      if (!response.ok) throw new Error("That sample could not be loaded.");
      await inspectNamed(file, new Uint8Array(await response.arrayBuffer()));
    } catch (error) {
      store.setLoadError(error instanceof Error ? error.message : "That sample could not be loaded.");
      store.setLoading(false);
    }
  }

  return (
    <div className="grid gap-8">
      <div className="max-w-2xl">
        <Meta>One drawing</Meta>
        <h1 className="mt-2 text-3xl font-medium tracking-tight">A quality report for one P&ID.</h1>
        <p className="mt-3 text-muted">
          Proteus XML is checked as data. A PDF stays a candidate list until you confirm it. Plant 3D
          arrives as JSON or CSV, because it does not export P&ID XML.
        </p>
      </div>

      <ol className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {STEPS.map(([title, body], index) => (
          <li key={title} className="rounded-xl border border-line bg-sheet px-4 py-3">
            <p className="font-mono text-xs text-oxide">0{index + 1}</p>
            <p className="mt-1 font-medium">{title}</p>
            <p className="mt-1 text-sm text-muted">{body}</p>
          </li>
        ))}
      </ol>

      <div className="grid items-start gap-4 lg:grid-cols-2">
        <div
          className={`rounded-xl border bg-sheet px-5 py-8 ${over ? "border-oxide bg-oxide-soft" : "border-dashed border-oxide"}`}
          onDragOver={(event) => {
            event.preventDefault();
            setOver(true);
          }}
          onDragLeave={() => setOver(false)}
          onDrop={(event) => {
            event.preventDefault();
            setOver(false);
            void takeFile(event.dataTransfer.files[0]);
          }}
        >
          <h2 className="text-lg font-medium">Drop a drawing file</h2>
          <p className="mt-2 max-w-md text-sm text-muted">
            Proteus or other XML, a Plant 3D JSON or CSV extract, or a PDF with a text layer. One file
            replaces the report.
          </p>
          <button
            type="button"
            disabled={loading}
            onClick={() => inputRef.current?.click()}
            className="mt-5 inline-flex h-11 items-center rounded-lg bg-oxide px-4 font-medium text-oxide-ink disabled:opacity-60"
          >
            {loading ? "Reading…" : "Choose a file"}
          </button>
          <input
            ref={inputRef}
            type="file"
            accept=".xml,.json,.csv,.pdf,application/xml,application/json,text/csv,application/pdf"
            className="sr-only"
            onChange={(event) => {
              void takeFile(event.target.files?.[0]);
              event.target.value = "";
            }}
          />
          {loadError ? <p className="mt-4 text-sm text-stamp">{loadError}</p> : null}
        </div>

        <div className="overflow-hidden rounded-xl border border-line bg-sheet">
          <div className="border-b border-line px-4 py-3">
            <h2 className="font-medium">Sample drawings</h2>
            <p className="text-sm text-muted">Public stand-ins, not plant records.</p>
          </div>
          <ul>
            {SAMPLES.map((sample) => (
              <li key={sample.id} className="border-b border-line last:border-b-0">
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => void takeSample(sample.file)}
                  className="flex min-h-11 w-full items-start gap-3 px-4 py-3 text-left hover:bg-paper disabled:opacity-60"
                >
                  <span className="w-20 shrink-0 pt-0.5 font-mono text-xs text-oxide">{sample.route}</span>
                  <span className="min-w-0">
                    <span className="block font-medium">{sample.title}</span>
                    <span className="mt-0.5 block text-sm text-muted">{sample.blurb}</span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
