import { format } from "date-fns";
import { KIND_ORDER, inCheckSet, type NormalizedModel } from "@/lib/inspector/types";
import { formatBytes, kindLabel, sourceLabel } from "@/lib/inspector/format";
import { useInspector } from "@/lib/inspector/store";
import { useReport } from "./use-report";
import { Meta, Panel, SeverityChip } from "./ui";

export function Overview() {
  const { model, findings } = useReport();
  if (!model) return null;
  const diag = model.diagnostics;
  const active = model.objects.filter(inCheckSet).length;
  const unreviewed = model.candidates.filter((candidate) => candidate.status === "unreviewed").length;
  const attention = findings.filter((finding) => finding.severity !== "info");
  const loaded = formatLoaded(diag.loadedAt);

  return (
    <div className="grid gap-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="In the check set" value={String(active)} note={`${diag.objectCount} loaded`} />
        <Stat
          label="Needs a look"
          value={String(attention.length)}
          note={attention.some((finding) => finding.severity === "error") ? "Includes errors" : "No errors"}
          emphasize={attention.length > 0}
        />
        <Stat label="Import warnings" value={String(diag.warnings.length)} note="Parser, not the sheet" />
        <Stat label="Unreviewed" value={String(unreviewed)} note={model.candidates.length ? "PDF candidates" : "None waiting"} />
      </div>

      {diag.stoppedOnError ? (
        <Panel className="border-stamp px-4 py-3">
          <Meta>Parser stopped</Meta>
          <p className="mt-2 text-sm">{diag.parseError ?? "The file did not load."}</p>
        </Panel>
      ) : null}

      <Panel className="px-4 py-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="font-medium">Import warnings</h2>
          <p className="text-sm text-muted">Not engineering findings.</p>
        </div>
        {diag.warnings.length ? (
          <ul className="mt-3 grid gap-3">
            {diag.warnings.map((warning) => (
              <li key={warning.id} className="border-l-2 border-oxide pl-3">
                <p className="font-mono text-xs tracking-wide text-oxide uppercase">Import warning</p>
                <p className="mt-1 text-sm">{warning.message}</p>
                {warning.detail ? <p className="mt-1 text-sm text-muted">{warning.detail}</p> : null}
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-sm text-muted">
            None. The file was read and this loader did not skip an unknown type or an unreadable property.
          </p>
        )}
      </Panel>

      {unreviewed ? (
        <Panel className="px-4 py-4">
          <h2 className="font-medium">{unreviewed} extracted tags are still unreviewed</h2>
          <p className="mt-1 text-sm text-muted">
            Recognition confidence is not engineering correctness. Nothing from the PDF enters the check set
            until you confirm it.
          </p>
          <button
            type="button"
            onClick={() => useInspector.getState().setTab("review")}
            className="mt-3 inline-flex h-11 items-center rounded-lg bg-oxide px-4 font-medium text-oxide-ink"
          >
            Review candidates
          </button>
        </Panel>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel className="px-4 py-4">
          <h2 className="font-medium">Objects by type</h2>
          <ul className="mt-3 grid gap-2">
            {KIND_ORDER.map((kind) => (
              <li key={kind} className="flex items-baseline justify-between gap-3 text-sm">
                <span>{kindLabel(kind)}</span>
                <span className="font-mono tabular-nums text-muted">{diag.countsByKind[kind]}</span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-muted">
            Counts are what the loader imported. PDF candidates are not included until confirmed.
          </p>
        </Panel>
        <Panel className="px-4 py-4">
          <h2 className="font-medium">First findings</h2>
          {attention.length ? (
            <ul className="mt-3 grid gap-3">
              {attention.slice(0, 5).map((finding) => (
                <li key={finding.id}>
                  <button
                    type="button"
                    onClick={() => {
                      if (finding.objectId) useInspector.getState().select(finding.objectId);
                      useInspector.getState().setTab("findings");
                    }}
                    className="flex w-full items-start gap-3 text-left"
                  >
                    <SeverityChip severity={finding.severity} />
                    <span className="min-w-0">
                      <span className="block font-mono text-sm">{finding.tag ?? finding.ruleLabel}</span>
                      <span className="mt-0.5 block text-sm text-muted">{finding.explanation}</span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 text-sm text-muted">No errors, warnings, or review items on this check set.</p>
          )}
        </Panel>
      </div>

      <p className="text-xs text-muted">
        {sourceLabel(diag.sourceKind)} · {diag.formatLabel} · {diag.parserName} {diag.parserVersion} · {formatBytes(diag.byteLength)} · {loaded}
      </p>
    </div>
  );
}

function Stat({
  label,
  value,
  note,
  emphasize = false,
}: {
  label: string;
  value: string;
  note: string;
  emphasize?: boolean;
}) {
  return (
    <div className="rounded-xl border border-line bg-sheet px-4 py-3">
      <p className="text-sm text-muted">{label}</p>
      <p className={`mt-1 font-mono text-2xl tabular-nums ${emphasize ? "text-stamp" : "text-ink"}`}>{value}</p>
      <p className="text-xs text-muted">{note}</p>
    </div>
  );
}

function formatLoaded(iso: string) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return format(date, "d MMM yyyy, HH:mm");
}

export function parserStatus(model: NormalizedModel) {
  if (model.diagnostics.stoppedOnError) return "Stopped on error";
  if (model.diagnostics.warnings.length) return "Loaded with import warnings";
  return "Loaded cleanly";
}
