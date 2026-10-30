import { formatBytes, sourceLabel } from "@/lib/inspector/format";
import { useReport } from "./use-report";
import { Meta, Panel } from "./ui";

export function ImportPanel() {
  const { model } = useReport();
  if (!model) return null;
  const diag = model.diagnostics;
  const rows: Array<[string, string]> = [
    ["File read", diag.fileRead ? `Yes, ${formatBytes(diag.byteLength)}` : "No"],
    ["Format", diag.formatLabel],
    ["Version", diag.formatVersion ?? "not stated"],
    ["Source route", sourceLabel(diag.sourceKind)],
    ["Parser", `${diag.parserName} ${diag.parserVersion}`],
    ["Originating system", diag.originatingSystem ?? "not available in imported data"],
    ["Drawing", diag.drawingName ?? "not named in the import"],
    ["Discipline", diag.discipline ?? "not available in imported data"],
    ["Objects loaded", String(diag.objectCount)],
    ["Stopped on error", diag.stoppedOnError ? "Yes" : "No"],
    ["Uninterpreted properties", String(diag.uninterpretedProperties)],
  ];

  return (
    <div className="grid gap-4">
      <Panel className="px-4 py-4">
        <Meta>Import diagnostics</Meta>
        <dl className="mt-3 grid gap-3 sm:grid-cols-2">
          {rows.map(([label, value]) => (
            <div key={label}>
              <dt className="text-xs text-muted">{label}</dt>
              <dd className="text-sm">{value}</dd>
            </div>
          ))}
        </dl>
        {diag.parseError ? <p className="mt-3 text-sm text-stamp">{diag.parseError}</p> : null}
      </Panel>
      <Panel className="px-4 py-4">
        <h2 className="font-medium">Skipped types</h2>
        {diag.skippedTypes.length ? (
          <ul className="mt-2 text-sm">
            {diag.skippedTypes.map((item) => (
              <li key={item.name}>
                {item.name} <span className="text-muted">({item.count})</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-2 text-sm text-muted">No unknown element types.</p>
        )}
      </Panel>
      <Panel className="px-4 py-4">
        <h2 className="font-medium">Parser scope</h2>
        <ul className="mt-2 grid gap-2 text-sm text-muted">
          {diag.scopeNotes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      </Panel>
    </div>
  );
}
