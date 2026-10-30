import type { Finding, NormalizedModel } from "./types";
import { severityLabel, showTag, showType, sourceLabel } from "./format";
import { KIND_ORDER } from "./types";

function esc(value: string): string {
  return value
    .replaceAll("&", "&" + "amp;")
    .replaceAll("<", "&" + "lt;")
    .replaceAll(">", "&" + "gt;")
    .replaceAll('"', "&" + "quot;")
    .replaceAll("'", "&" + "#39;");
}

export function reportHtml(model: NormalizedModel, findings: Finding[], ruleSetName: string): string {
  const diag = model.diagnostics;
  const active = model.objects.filter((obj) => obj.reviewStatus === "native" || obj.reviewStatus === "confirmed");
  const rows = active
    .map(
      (obj) => `<tr>
        <td>${esc(showTag(obj))}</td>
        <td>${esc(obj.kind)}</td>
        <td>${esc(showType(obj))}</td>
        <td>${esc(obj.id)}</td>
        <td>${esc(obj.sourcePath)}</td>
      </tr>`,
    )
    .join("");
  const warningRows = diag.warnings
    .map(
      (warning) => `<li><strong>Import warning.</strong> ${esc(warning.message)}${warning.detail ? ` <span class="muted">${esc(warning.detail)}</span>` : ""}</li>`,
    )
    .join("");
  const findingRows = findings
    .map(
      (finding) => `<tr>
        <td>${esc(severityLabel(finding.severity))}</td>
        <td>${esc(finding.tag ?? "—")}</td>
        <td>${esc(finding.ruleLabel)}${finding.projectCheck ? " · project check" : ""}</td>
        <td>${esc(finding.explanation)}</td>
      </tr>`,
    )
    .join("");
  const counts = KIND_ORDER.map((kind) => `${diag.countsByKind[kind]} ${kind}`).join(", ");
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>Ledger report — ${esc(diag.fileName)}</title>
  <style>
    body { margin: 0; background: #f3efe6; color: #1c2430; font: 15px/1.5 "IBM Plex Sans", "Segoe UI", sans-serif; }
    main { max-width: 920px; margin: 0 auto; padding: 32px 20px 64px; }
    h1 { font-size: 28px; font-weight: 500; margin: 0 0 4px; }
    h2 { font-size: 18px; font-weight: 500; margin: 28px 0 8px; }
    .muted { color: #5c6670; }
    .rule { height: 6px; background: #1b4f48; margin: -32px -20px 24px; }
    table { width: 100%; border-collapse: collapse; background: #fffdf8; }
    th, td { text-align: left; vertical-align: top; border-bottom: 1px solid #e3d9c8; padding: 8px 10px; font-size: 14px; }
    th { font-size: 12px; letter-spacing: 0.04em; text-transform: uppercase; color: #5c6670; }
    ul { padding-left: 18px; }
    code { font-family: "IBM Plex Mono", ui-monospace, monospace; }
  </style>
</head>
<body>
  <main>
    <div class="rule"></div>
    <p class="muted">Ledger · P&ID quality report</p>
    <h1>${esc(diag.fileName)}</h1>
    <p class="muted">${esc(sourceLabel(diag.sourceKind))} · ${esc(diag.formatLabel)} · ${esc(diag.parserName)} ${esc(diag.parserVersion)}</p>
    <p>Drawing: ${esc(diag.drawingName ?? "not named in the import")} · Rule set: ${esc(ruleSetName)} · Loaded ${esc(diag.loadedAt)}</p>
    <h2>Summary</h2>
    <p>File read: ${diag.fileRead ? "yes" : "no"}. Parser stopped on error: ${diag.stoppedOnError ? "yes" : "no"}. Objects loaded: ${diag.objectCount} (${esc(counts)}). Findings: ${findings.length}. Import warnings: ${diag.warnings.length}.</p>
    ${diag.parseError ? `<p>Parse error: ${esc(diag.parseError)}</p>` : ""}
    <h2>Import warnings</h2>
    ${warningRows ? `<ul>${warningRows}</ul>` : "<p>No import warnings.</p>"}
    <h2>Tag and object inventory</h2>
    <table>
      <thead><tr><th>Tag</th><th>Type</th><th>Class</th><th>ID</th><th>Source</th></tr></thead>
      <tbody>${rows || `<tr><td colspan="5">No objects in the check set.</td></tr>`}</tbody>
    </table>
    <h2>Findings</h2>
    <table>
      <thead><tr><th>Severity</th><th>Tag</th><th>Rule</th><th>Explanation</th></tr></thead>
      <tbody>${findingRows}</tbody>
    </table>
    <p class="muted">Project checks are the active rule set, not a DEXPI conformance test. Import warnings are parser and format limits.</p>
  </main>
</body>
</html>`;
}

export function findingsCsv(findings: Finding[]): string {
  const lines = [["severity", "tag", "rule", "project_check", "object_id", "explanation", "source"]];
  for (const finding of findings) {
    lines.push([
      finding.severity,
      finding.tag ?? "",
      finding.ruleLabel,
      finding.projectCheck ? "yes" : "no",
      finding.objectId ?? "",
      finding.explanation,
      finding.sourceRef ?? "",
    ]);
  }
  return lines.map((row) => row.map(csvCell).join(",")).join("\n");
}

function csvCell(value: string): string {
  if (/[",\n]/.test(value)) return `"${value.replace(/"/g, '""')}"`;
  return value;
}

export function downloadText(filename: string, content: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
