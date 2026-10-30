import { RULE_SETS } from "@/lib/inspector/rules";
import type { Severity } from "@/lib/inspector/types";
import { severityLabel } from "@/lib/inspector/format";
import { useInspector } from "@/lib/inspector/store";
import { useReport } from "./use-report";
import { Panel } from "./ui";

const SEVERITIES: Severity[] = ["error", "warning", "review", "info"];

export function RulesPanel() {
  const { rules } = useReport();
  const ruleSetId = useInspector((state) => state.ruleSetId);
  const setRuleSet = useInspector((state) => state.setRuleSet);
  const toggleRule = useInspector((state) => state.toggleRule);
  const setSeverity = useInspector((state) => state.setSeverity);
  const active = RULE_SETS.find((set) => set.id === ruleSetId) ?? RULE_SETS[0];

  return (
    <div className="grid gap-4">
      <Panel className="px-4 py-4">
        <h2 className="font-medium">Project standard</h2>
        <p className="mt-1 text-sm text-muted">
          Field rules are yours. They are not DEXPI conformance checks. Broken references and connection
          reviews always run. Import warnings stay on the Import tab.
        </p>
        <label className="mt-4 block text-sm">
          Rule set
          <select
            value={ruleSetId}
            onChange={(event) => setRuleSet(event.target.value)}
            className="mt-1 h-11 w-full rounded-lg border border-line bg-sheet px-3"
          >
            {RULE_SETS.map((set) => (
              <option key={set.id} value={set.id}>
                {set.name}
              </option>
            ))}
          </select>
        </label>
        <p className="mt-2 text-sm text-muted">{active.description}</p>
      </Panel>
      <Panel>
        <ul>
          {rules.map((rule) => (
            <li key={rule.id} className="grid gap-3 border-b border-line px-4 py-3 last:border-b-0 sm:grid-cols-[1fr_auto] sm:items-center">
              <div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={rule.enabled}
                  onClick={() => toggleRule(rule.id, !rule.enabled)}
                  className="flex min-h-11 items-center gap-3 text-left"
                >
                  <span
                    className={`relative h-6 w-11 shrink-0 rounded-full ${rule.enabled ? "bg-oxide" : "bg-line"}`}
                  >
                    <span
                      className={`absolute top-0.5 size-5 rounded-full bg-sheet ${rule.enabled ? "left-5" : "left-0.5"}`}
                    />
                  </span>
                  <span>
                    <span className="block font-medium">{rule.label}</span>
                    <span className="block text-sm text-muted">{rule.detail}</span>
                  </span>
                </button>
              </div>
              <label className="text-sm text-muted">
                Severity
                <select
                  value={rule.severity}
                  disabled={!rule.enabled}
                  onChange={(event) => setSeverity(rule.id, event.target.value as Severity)}
                  className="mt-1 h-11 w-full rounded-lg border border-line bg-sheet px-3 text-ink disabled:opacity-50 sm:w-36"
                >
                  {SEVERITIES.map((severity) => (
                    <option key={severity} value={severity}>
                      {severityLabel(severity)}
                    </option>
                  ))}
                </select>
              </label>
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  );
}
