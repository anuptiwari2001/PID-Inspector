import type { Rule, RuleSet, Severity } from "./types";

const processRules: Rule[] = [
  {
    id: "eq-tag",
    label: "Equipment tag",
    detail: "Equipment must have a tag.",
    appliesTo: "equipment",
    check: "tag",
    severity: "error",
    enabled: true,
  },
  {
    id: "eq-type",
    label: "Equipment type",
    detail: "Equipment must have a specific class, not a generic Equipment element.",
    appliesTo: "equipment",
    check: "specific-type",
    severity: "error",
    enabled: true,
  },
  {
    id: "eq-service",
    label: "Equipment service",
    detail: "Equipment must have a service value.",
    appliesTo: "equipment",
    check: "service",
    severity: "warning",
    enabled: true,
  },
  {
    id: "valve-tag",
    label: "Valve tag",
    detail: "A valve must have a tag.",
    appliesTo: "valve",
    check: "tag",
    severity: "error",
    enabled: true,
  },
  {
    id: "valve-type",
    label: "Valve type",
    detail: "A valve must have a specific type, not only Valve.",
    appliesTo: "valve",
    check: "specific-type",
    severity: "warning",
    enabled: true,
  },
  {
    id: "valve-service",
    label: "Valve service",
    detail: "A valve must have a service value.",
    appliesTo: "valve",
    check: "service",
    severity: "warning",
    enabled: true,
  },
  {
    id: "line-number",
    label: "Line number",
    detail: "A line must have a line number. Segments inherit it from their piping system.",
    appliesTo: "piping",
    check: "line-number",
    severity: "error",
    enabled: true,
  },
  {
    id: "inst-tag",
    label: "Instrument tag",
    detail: "An instrument must have a tag.",
    appliesTo: "instrument",
    check: "tag",
    severity: "error",
    enabled: true,
  },
  {
    id: "inst-function",
    label: "Instrument function",
    detail: "An instrument must have a function, or a specific class that already states it.",
    appliesTo: "instrument",
    check: "instrument-function",
    severity: "warning",
    enabled: true,
  },
];

function withEnabled(ids: string[]): Rule[] {
  const on = new Set(ids);
  return processRules.map((rule) => ({ ...rule, enabled: on.has(rule.id) }));
}

export const RULE_SETS: RuleSet[] = [
  {
    id: "process",
    name: "Process project standard",
    description:
      "Tags, classes, line numbers, valve type, instrument function, and service. These are project checks, not universal DEXPI rules.",
    rules: processRules,
  },
  {
    id: "identity",
    name: "Identity only",
    description: "Tags and line numbers only. Reference errors and connection reviews still run.",
    rules: withEnabled(["eq-tag", "valve-tag", "line-number", "inst-tag"]),
  },
];

export interface RuleOverrides {
  [ruleId: string]: { enabled?: boolean; severity?: Severity };
}

export function effectiveRules(ruleSetId: string, overrides: RuleOverrides): Rule[] {
  const set = RULE_SETS.find((item) => item.id === ruleSetId) ?? RULE_SETS[0];
  return set.rules.map((rule) => {
    const override = overrides[rule.id];
    if (!override) return { ...rule };
    return {
      ...rule,
      enabled: override.enabled ?? rule.enabled,
      severity: override.severity ?? rule.severity,
    };
  });
}
