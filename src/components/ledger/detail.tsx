import { connectionSummary, showProperty, showTag, showType, kindLabel } from "@/lib/inspector/format";
import { useInspector } from "@/lib/inspector/store";
import { useReport } from "./use-report";
import { Panel, SeverityChip } from "./ui";

export function Detail() {
  const { model, findings, byId } = useReport();
  const selectedId = useInspector((state) => state.selectedId);
  const obj = selectedId ? byId.get(selectedId) : undefined;
  if (!model) return null;
  if (!obj) {
    return (
      <Panel className="hidden px-4 py-4 lg:block">
        <p className="text-sm text-muted">Select a tag to see its source, properties, and connections.</p>
      </Panel>
    );
  }
  const related = findings.filter((finding) => finding.objectId === obj.id);

  return (
    <Panel className="px-4 py-4">
      <p className="font-mono text-xs text-muted">{kindLabel(obj.kind)}</p>
      <h2 className="mt-1 font-mono text-xl">{showTag(obj)}</h2>
      <p className="text-sm text-muted">{showType(obj)}</p>
      {obj.reviewStatus === "confirmed" ? (
        <p className="mt-2 text-xs text-oxide">Designer confirmed. Not native source data.</p>
      ) : null}
      {obj.confidence != null ? (
        <p className="mt-2 text-sm text-muted">
          Recognition confidence {Math.round(obj.confidence * 100)}%. That is not an engineering approval.
        </p>
      ) : null}
      {obj.hint ? <p className="mt-2 text-sm">{obj.hint}</p> : null}
      <dl className="mt-4 grid gap-2 text-sm">
        <div>
          <dt className="text-xs text-muted">Object ID</dt>
          <dd className="font-mono break-all">{obj.id}</dd>
        </div>
        <div>
          <dt className="text-xs text-muted">Source</dt>
          <dd className="break-all">{obj.sourcePath}</dd>
        </div>
        <div>
          <dt className="text-xs text-muted">Location</dt>
          <dd>{obj.location ?? "Drawing coordinates are not available in the imported data."}</dd>
        </div>
      </dl>
      <h3 className="mt-4 text-sm font-medium">Properties</h3>
      {obj.properties.length ? (
        <ul className="mt-2 grid gap-2 text-sm">
          {obj.properties.map((property) => (
            <li key={`${property.set ?? ""}-${property.name}`} className="flex items-baseline justify-between gap-3">
              <span className="text-muted">{property.label}</span>
              <span className="text-right">{showProperty(property)}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-muted">No properties were imported for this object.</p>
      )}
      <h3 className="mt-4 text-sm font-medium">Connections</h3>
      <p className="mt-1 text-sm">{connectionSummary(obj, byId)}</p>
      {related.length ? (
        <ul className="mt-4 grid gap-2">
          {related.map((finding) => (
            <li key={finding.id} className="flex items-start gap-2">
              <SeverityChip severity={finding.severity} />
              <span className="text-sm text-muted">{finding.explanation}</span>
            </li>
          ))}
        </ul>
      ) : null}
    </Panel>
  );
}
