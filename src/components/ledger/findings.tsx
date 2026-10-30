import { useState } from "react";
import type { Severity } from "@/lib/inspector/types";
import { useInspector } from "@/lib/inspector/store";
import { useReport } from "./use-report";
import { Panel, SeverityChip } from "./ui";

const FILTERS: Array<Severity | "all"> = ["all", "error", "warning", "review", "info"];

export function Findings() {
  const { findings } = useReport();
  const query = useInspector((state) => state.query);
  const [filter, setFilter] = useState<Severity | "all">("all");
  const needle = query.trim().toLowerCase();
  const rows = findings.filter((finding) => {
    if (filter !== "all" && finding.severity !== filter) return false;
    if (!needle) return true;
    return `${finding.tag ?? ""} ${finding.ruleLabel} ${finding.explanation}`.toLowerCase().includes(needle);
  });

  return (
    <div className="grid gap-3">
      <div className="flex gap-2 overflow-x-auto">
        {FILTERS.map((item) => (
          <button
            key={item}
            type="button"
            aria-pressed={filter === item}
            onClick={() => setFilter(item)}
            className={`inline-flex h-11 shrink-0 items-center rounded-lg border px-3 text-sm capitalize ${filter === item ? "border-oxide bg-oxide-soft text-oxide" : "border-line bg-sheet text-muted"}`}
          >
            {item === "all" ? "All" : item}
          </button>
        ))}
      </div>
      <Panel>
        <ul>
          {rows.length ? (
            rows.map((finding) => (
              <li key={finding.id} className="border-b border-line last:border-b-0">
                <button
                  type="button"
                  onClick={() => finding.objectId && useInspector.getState().select(finding.objectId)}
                  className="flex w-full items-start gap-3 px-4 py-3 text-left"
                >
                  <SeverityChip severity={finding.severity} />
                  <span className="min-w-0">
                    <span className="flex flex-wrap items-baseline gap-2">
                      <span className="font-mono text-sm">{finding.tag ?? "—"}</span>
                      <span className="text-sm font-medium">{finding.ruleLabel}</span>
                      <span className="text-xs text-muted">{finding.projectCheck ? "Project check" : "Data check"}</span>
                    </span>
                    <span className="mt-1 block text-sm text-muted">{finding.explanation}</span>
                  </span>
                </button>
              </li>
            ))
          ) : (
            <li className="px-4 py-6 text-sm text-muted">No findings in this filter.</li>
          )}
        </ul>
      </Panel>
    </div>
  );
}
