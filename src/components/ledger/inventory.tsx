import { useMemo, useState } from "react";
import { connectionSummary, keyProperties, kindLabel, showTag, showType } from "@/lib/inspector/format";
import { KIND_ORDER, inCheckSet, type ObjectKind } from "@/lib/inspector/types";
import { useInspector } from "@/lib/inspector/store";
import { useReport } from "./use-report";
import { SeverityChip } from "./ui";

const DEFAULT_KINDS: ObjectKind[] = ["equipment", "piping", "valve", "instrument"];

export function Inventory() {
  const { model, findings, byId } = useReport();
  const query = useInspector((state) => state.query);
  const selectedId = useInspector((state) => state.selectedId);
  const [kinds, setKinds] = useState<ObjectKind[]>(DEFAULT_KINDS);
  const rows = useMemo(() => {
    if (!model) return [];
    const needle = query.trim().toLowerCase();
    return model.objects.filter((obj) => {
      if (!inCheckSet(obj) || !kinds.includes(obj.kind)) return false;
      if (!needle) return true;
      const blob = [obj.tag, obj.id, obj.objectType, obj.kind, ...obj.properties.map((property) => property.value)]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return blob.includes(needle);
    });
  }, [model, query, kinds]);

  if (!model) return null;

  return (
    <div className="grid gap-3">
      <div className="flex gap-2 overflow-x-auto pb-1">
        {KIND_ORDER.map((kind) => {
          const on = kinds.includes(kind);
          return (
            <button
              key={kind}
              type="button"
              aria-pressed={on}
              onClick={() =>
                setKinds((current) =>
                  current.includes(kind) ? current.filter((item) => item !== kind) : [...current, kind],
                )
              }
              className={`inline-flex h-11 shrink-0 items-center rounded-lg border px-3 text-sm ${on ? "border-oxide bg-oxide-soft text-oxide" : "border-line bg-sheet text-muted"}`}
            >
              {kindLabel(kind)}
            </button>
          );
        })}
      </div>
      <div className="overflow-x-auto rounded-xl border border-line bg-sheet">
        <table className="w-full min-w-[44rem] border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-line text-xs tracking-wide text-muted uppercase">
              <th className="px-3 py-3 font-medium">Tag</th>
              <th className="px-3 py-3 font-medium">Type</th>
              <th className="px-3 py-3 font-medium">Class</th>
              <th className="px-3 py-3 font-medium">Key properties</th>
              <th className="px-3 py-3 font-medium">Connections</th>
            </tr>
          </thead>
          <tbody>
            {rows.length ? (
              rows.map((obj) => {
                const hit = findings.find((finding) => finding.objectId === obj.id && finding.severity !== "info");
                const selected = obj.id === selectedId;
                return (
                  <tr
                    key={obj.id}
                    className={`border-b border-line last:border-b-0 ${selected ? "bg-oxide-soft" : "hover:bg-paper"}`}
                  >
                    <td className="px-3 py-2">
                      <button
                        type="button"
                        onClick={() => useInspector.getState().select(obj.id)}
                        className="inline-flex min-h-11 items-center gap-2 text-left font-mono"
                      >
                        {showTag(obj)}
                        {hit ? <SeverityChip severity={hit.severity} /> : null}
                      </button>
                    </td>
                    <td className="px-3 py-2">{kindLabel(obj.kind)}</td>
                    <td className="px-3 py-2">{showType(obj)}</td>
                    <td className="px-3 py-2 text-muted">{keyProperties(obj)}</td>
                    <td className="px-3 py-2">{connectionSummary(obj, byId)}</td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={5} className="px-3 py-6 text-muted">
                  Nothing in this filter. Missing tags are shown as “missing” — they are not guessed.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
