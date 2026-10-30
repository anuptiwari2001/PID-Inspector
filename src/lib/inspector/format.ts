import type { EngObject, ObjectKind, PropertyEntry, Severity, SourceKind } from "./types";

const LABELS: Record<string, string> = {
  TagNameAssignmentClass: "Tag",
  LineNumberAssignmentClass: "Line number",
  FluidCodeAssignmentClass: "Fluid code",
  PipingComponentNumberAssignmentClass: "Component number",
  ProcessInstrumentationFunctionNumberAssignmentClass: "Instrument number",
  ProcessInstrumentationFunctionCategoryAssignmentClass: "Function",
  NominalDiameterNumericalValueRepresentationAssignmentClass: "Nominal diameter",
  NominalDiameterStandardRepresentationAssignmentClass: "Nominal diameter",
  ServiceAssignmentClass: "Service",
  ValveTypeAssignmentClass: "Valve type",
  FailActionAssignmentClass: "Fail action",
};

export function labelFor(name: string): string {
  if (LABELS[name]) return LABELS[name];
  const trimmed = name.replace(/AssignmentClass$/, "").replace(/_/g, " ");
  return trimmed.replace(/([a-z])([A-Z])/g, "$1 $2").trim() || name;
}

export function showProperty(property: PropertyEntry): string {
  if (property.status === "blank") return "blank";
  if (property.status === "uninterpreted") return "not interpreted";
  if (property.value == null || property.value.trim() === "") return "missing";
  return property.value;
}

export function showType(obj: EngObject): string {
  return obj.objectType.trim() ? obj.objectType : "not available in imported data";
}

export function showTag(obj: EngObject): string {
  return obj.tag ?? "missing";
}

export function kindLabel(kind: ObjectKind): string {
  if (kind === "piping") return "Piping";
  return kind.slice(0, 1).toUpperCase() + kind.slice(1);
}

export function keyProperties(obj: EngObject): string {
  const tests = [/service/i, /fluid/i, /function|category/i, /diameter/i, /valve type/i, /size/i];
  const bits: string[] = [];
  for (const test of tests) {
    const property = obj.properties.find(
      (entry) => test.test(entry.name) || test.test(entry.label),
    );
    if (!property) continue;
    bits.push(`${property.label}: ${showProperty(property)}`);
    if (bits.length === 3) break;
  }
  return bits.length ? bits.join(" · ") : "not available in imported data";
}

export function severityLabel(severity: Severity): string {
  if (severity === "info") return "Info";
  if (severity === "review") return "Review";
  if (severity === "warning") return "Warning";
  return "Error";
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function displayName(obj: EngObject): string {
  return obj.tag ?? obj.id;
}

export function endpointLabel(
  id: string,
  byId: Map<string, EngObject>,
): string {
  const obj = byId.get(id);
  if (!obj) return `${id} (not imported)`;
  if (obj.objectType === "PipingNetworkSegment" && obj.parentId) {
    const parent = byId.get(obj.parentId);
    if (parent?.tag) return parent.tag;
  }
  if (obj.kind === "nozzle" && obj.parentId) {
    const parent = byId.get(obj.parentId);
    if (parent) return `${parent.tag ?? parent.id} nozzle`;
  }
  return obj.tag ?? obj.id;
}

export function connectionSummary(obj: EngObject, byId: Map<string, EngObject>): string {
  if (!obj.connections.length) return "none recorded";
  const labels: string[] = [];
  for (const link of obj.connections) {
    const label = endpointLabel(link.targetId, byId);
    if (!labels.includes(label)) labels.push(label);
  }
  const shown = labels.slice(0, 4);
  const extra = labels.length > shown.length ? ` +${labels.length - shown.length}` : "";
  return shown.join(", ") + extra;
}


export function sourceLabel(kind: SourceKind): string {
  if (kind === "proteus") return "Proteus XML";
  if (kind === "dexpi2") return "DEXPI 2 scan";
  if (kind === "pdf") return "PDF text layer";
  if (kind === "autocad-json") return "Plant 3D JSON";
  if (kind === "autocad-csv") return "Data Manager CSV";
  return "Unrecognized file";
}

