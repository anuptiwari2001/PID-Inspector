import { useRef } from "react";
import { downloadText, findingsCsv, reportHtml } from "@/lib/inspector/report";
import { sourceLabel } from "@/lib/inspector/format";
import type { LedgerTab } from "@/lib/inspector/store";
import { useInspector } from "@/lib/inspector/store";
import { inspectNamed } from "@/lib/inspector/client";
import { useReport } from "./use-report";
import { parserStatus } from "./overview";
import { Overview } from "./overview";
import { Inventory } from "./inventory";
import { Connections } from "./connections";
import { Findings } from "./findings";
import { ImportPanel } from "./import-panel";
import { RulesPanel } from "./rules-panel";
import { Candidates } from "./candidates";
import { Detail } from "./detail";

export function ReportView() {
  const { model, findings, ruleSet } = useReport();
  const tab = useInspector((state) => state.tab);
  const query = useInspector((state) => state.query);
  const loading = useInspector((state) => state.loading);
  const inputRef = useRef<HTMLInputElement>(null);
  if (!model) return null;
  const diag = model.diagnostics;
  const unreviewed = model.candidates.filter((candidate) => candidate.status === "unreviewed").length;
  const attention = findings.filter((finding) => finding.severity !== "info").length;
  const tabs: Array<{ id: LedgerTab; label: string; count?: number }> = [
    { id: "overview", label: "Overview" },
    { id: "inventory", label: "Inventory" },
    { id: "connections", label: "Connections" },
    { id: "findings", label: "Findings", count: attention },
    ...(model.candidates.length ? [{ id: "review" as const, label: "Review", count: unreviewed }] : []),
    { id: "import", label: "Import", count: diag.warnings.length },
    { id: "rules", label: "Rules" },
  ];

  function save(kind: "html" | "csv" | "json") {
    const base = diag.fileName.replace(/\.[^.]+$/, "") || "drawing";
    if (kind === "html") {
      downloadText(`${base}-ledger.html`, reportHtml(model!, findings, ruleSet.name), "text/html");
    } else if (kind === "csv") {
      downloadText(`${base}-findings.csv`, findingsCsv(findings), "text/csv");
    } else {
      downloadText(`${base}-model.json`, JSON.stringify(model, null, 2), "application/json");
    }
  }

  return (
    <div className="grid gap-4">
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_16rem]">
        <div>
          <p className="font-mono text-xs tracking-wide text-muted uppercase">{sourceLabel(diag.sourceKind)}</p>
          <h1 className="mt-1 text-2xl font-medium break-words">{diag.fileName}</h1>
          <p className="mt-1 text-sm text-muted">
            {diag.drawingName ?? "Drawing name not in the import"} · {parserStatus(model)}
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <button type="button" onClick={() => save("html")} className="inline-flex h-11 items-center rounded-lg bg-oxide px-3 text-sm font-medium text-oxide-ink">
              HTML report
            </button>
            <button type="button" onClick={() => save("csv")} className="inline-flex h-11 items-center rounded-lg border border-line bg-sheet px-3 text-sm">
              Findings CSV
            </button>
            <button type="button" onClick={() => save("json")} className="inline-flex h-11 items-center rounded-lg border border-line bg-sheet px-3 text-sm">
              JSON
            </button>
            <button
              type="button"
              disabled={loading}
              onClick={() => inputRef.current?.click()}
              className="inline-flex h-11 items-center rounded-lg border border-line bg-sheet px-3 text-sm disabled:opacity-60"
            >
              {loading ? "Reading…" : "Replace file"}
            </button>
            <button
              type="button"
              onClick={() => useInspector.getState().clear()}
              className="inline-flex h-11 items-center rounded-lg px-3 text-sm text-muted"
            >
              Close
            </button>
            <input
              ref={inputRef}
              type="file"
              accept=".xml,.json,.csv,.pdf"
              className="sr-only"
              onChange={(event) => {
                const file = event.target.files?.[0];
                event.target.value = "";
                if (!file) return;
                void file.arrayBuffer().then((buffer) => inspectNamed(file.name, new Uint8Array(buffer)));
              }}
            />
          </div>
        </div>
        <aside className="rounded-xl border border-ink bg-sheet">
          <TitleRow label="Drawing" value={diag.drawingName ?? "Not named"} />
          <TitleRow label="Format" value={diag.formatLabel} />
          <TitleRow label="Parser" value={parserStatus(model)} last />
        </aside>
      </div>

      <label className="block">
        <span className="sr-only">Search tags and findings</span>
        <input
          value={query}
          onChange={(event) => useInspector.getState().setQuery(event.target.value)}
          placeholder="Search tags, classes, findings"
          className="h-11 w-full rounded-lg border border-line bg-sheet px-3"
        />
      </label>

      <div role="tablist" aria-label="Report sections" className="flex gap-1 overflow-x-auto border-b border-line">
        {tabs.map((item) => {
          const selected = tab === item.id;
          return (
            <button
              key={item.id}
              type="button"
              role="tab"
              aria-selected={selected}
              onClick={() => useInspector.getState().setTab(item.id)}
              className={`inline-flex h-11 shrink-0 items-center gap-2 border-b-2 px-3 text-sm ${selected ? "border-oxide font-medium text-oxide" : "border-transparent text-muted"}`}
            >
              {item.label}
              {item.count ? <span className="font-mono text-xs tabular-nums">{item.count}</span> : null}
            </button>
          );
        })}
      </div>

      <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <div className="min-w-0">
          {tab === "overview" ? <Overview /> : null}
          {tab === "inventory" ? <Inventory /> : null}
          {tab === "connections" ? <Connections /> : null}
          {tab === "findings" ? <Findings /> : null}
          {tab === "review" ? <Candidates /> : null}
          {tab === "import" ? <ImportPanel /> : null}
          {tab === "rules" ? <RulesPanel /> : null}
        </div>
        <Detail />
      </div>
    </div>
  );
}

function TitleRow({ label, value, last = false }: { label: string; value: string; last?: boolean }) {
  return (
    <div className={`px-4 py-3 ${last ? "" : "border-b border-line"}`}>
      <p className="font-mono text-xs tracking-wide text-muted uppercase">{label}</p>
      <p className="mt-1 text-sm break-words">{value}</p>
    </div>
  );
}
