import { useMemo } from "react";
import { effectiveRules, RULE_SETS } from "@/lib/inspector/rules";
import { useInspector } from "@/lib/inspector/store";

export function useReport() {
  const model = useInspector((state) => state.model);
  const findings = useInspector((state) => state.findings);
  const ruleSetId = useInspector((state) => state.ruleSetId);
  const overrides = useInspector((state) => state.overrides);
  const rules = useMemo(() => effectiveRules(ruleSetId, overrides), [ruleSetId, overrides]);
  const byId = useMemo(() => new Map(model?.objects.map((obj) => [obj.id, obj]) ?? []), [model]);
  const ruleSet = RULE_SETS.find((set) => set.id === ruleSetId) ?? RULE_SETS[0];
  return { model, rules, findings, byId, ruleSet };
}
