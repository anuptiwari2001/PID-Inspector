export const LEDGER_VERSION = "0.1.0";

export type SourceKind =
  | "proteus"
  | "dexpi2"
  | "pdf"
  | "autocad-json"
  | "autocad-csv"
  | "unknown";

export type ObjectKind =
  | "equipment"
  | "piping"
  | "valve"
  | "instrument"
  | "nozzle"
  | "other";

export type Severity = "error" | "warning" | "review" | "info";

export type ReviewStatus = "native" | "confirmed" | "unreviewed" | "rejected";

export type PropertyStatus = "ok" | "blank" | "uninterpreted";

export interface ImportWarning {
  id: string;
  code: string;
  message: string;
  detail?: string;
}

export interface PropertyEntry {
  name: string;
  label: string;
  value: string | null;
  format?: string;
  set?: string;
  status: PropertyStatus;
}

export interface ConnectionRef {
  targetId: string;
  targetTag: string | null;
  relation: string;
}

export interface EngObject {
  id: string;
  tag: string | null;
  kind: ObjectKind;
  objectType: string;
  componentName: string | null;
  properties: PropertyEntry[];
  connections: ConnectionRef[];
  parentId: string | null;
  reviewStatus: ReviewStatus;
  confidence: number | null;
  page: number | null;
  location: string | null;
  sourceElement: string;
  sourcePath: string;
  drawing: string | null;
  hint: string | null;
}

export interface Edge {
  id: string;
  ownerId: string;
  fromId: string;
  toId: string;
  fromNode?: string;
  toNode?: string;
  sourcePath: string;
}

export interface Candidate {
  id: string;
  rawText: string;
  context: string;
  suggestedTag: string;
  suggestedKind: ObjectKind;
  suggestedType: string;
  confidence: number;
  page: number;
  location: string;
  status: "unreviewed" | "confirmed" | "rejected";
  service?: string;
  functionName?: string;
  mentionedEnds?: string;
  hint?: string;
}

export interface TranscriptLine {
  page: number;
  text: string;
}

export interface ImportDiagnostics {
  fileRead: boolean;
  fileName: string;
  byteLength: number;
  sourceKind: SourceKind;
  formatLabel: string;
  formatVersion: string | null;
  parserName: string;
  parserVersion: string;
  originatingSystem: string | null;
  drawingName: string | null;
  discipline: string | null;
  objectCount: number;
  countsByKind: Record<ObjectKind, number>;
  skippedTypes: { name: string; count: number }[];
  uninterpretedProperties: number;
  stoppedOnError: boolean;
  parseError: string | null;
  warnings: ImportWarning[];
  scopeNotes: string[];
  loadedAt: string;
}

export interface NormalizedModel {
  diagnostics: ImportDiagnostics;
  objects: EngObject[];
  edges: Edge[];
  candidates: Candidate[];
  transcript: TranscriptLine[];
}

export type FieldCheck =
  | "tag"
  | "specific-type"
  | "line-number"
  | "instrument-function"
  | "service";

export interface Rule {
  id: string;
  label: string;
  detail: string;
  appliesTo: ObjectKind;
  check: FieldCheck;
  severity: Severity;
  enabled: boolean;
}

export interface RuleSet {
  id: string;
  name: string;
  description: string;
  rules: Rule[];
}

export type FindingCategory =
  | "import"
  | "connection"
  | "field"
  | "identity"
  | "inventory";

export interface Finding {
  id: string;
  severity: Severity;
  ruleId: string;
  ruleLabel: string;
  category: FindingCategory;
  projectCheck: boolean;
  objectId?: string;
  tag: string | null;
  explanation: string;
  sourceRef?: string;
}

export const KIND_ORDER: ObjectKind[] = [
  "equipment",
  "piping",
  "valve",
  "instrument",
  "nozzle",
  "other",
];

export function emptyCounts(): Record<ObjectKind, number> {
  return {
    equipment: 0,
    piping: 0,
    valve: 0,
    instrument: 0,
    nozzle: 0,
    other: 0,
  };
}

export function countKinds(objects: EngObject[]): Record<ObjectKind, number> {
  const counts = emptyCounts();
  for (const obj of objects) counts[obj.kind] += 1;
  return counts;
}

export function inCheckSet(obj: EngObject): boolean {
  return obj.reviewStatus === "native" || obj.reviewStatus === "confirmed";
}
