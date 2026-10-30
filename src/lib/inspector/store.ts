import { create } from "zustand";
import type { Finding, NormalizedModel, Severity } from "./types";
import type { RuleOverrides } from "./rules";
import { RULE_SETS } from "./rules";

export type LedgerTab =
  | "overview"
  | "inventory"
  | "connections"
  | "findings"
  | "review"
  | "import"
  | "rules";

const STORAGE_KEY = "ledger-rules-v1";

interface PersistedRules {
  ruleSetId: string;
  overrides: RuleOverrides;
}

interface InspectorState {
  model: NormalizedModel | null;
  findings: Finding[];
  loading: boolean;
  loadError: string | null;
  ruleSetId: string;
  overrides: RuleOverrides;
  selectedId: string | null;
  query: string;
  tab: LedgerTab;
  setTab: (tab: LedgerTab) => void;
  setQuery: (query: string) => void;
  select: (id: string | null) => void;
  setLoading: (loading: boolean) => void;
  setLoadError: (loadError: string | null) => void;
  setReport: (model: NormalizedModel, findings: Finding[], options?: { keepPlace?: boolean }) => void;
  setFindings: (findings: Finding[]) => void;
  clear: () => void;
  setRuleSet: (ruleSetId: string) => void;
  toggleRule: (ruleId: string, enabled: boolean) => void;
  setSeverity: (ruleId: string, severity: Severity) => void;
  setCandidate: (id: string, status: "unreviewed" | "confirmed" | "rejected") => void;
  confirmHigh: () => void;
  hydrate: () => void;
}

function persist(ruleSetId: string, overrides: RuleOverrides) {
  try {
    const payload: PersistedRules = { ruleSetId, overrides };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  } catch {
    // The report still works if storage is blocked.
  }
}

function rerun() {
  void import("./client").then(({ refreshFindings }) => refreshFindings());
}

export const useInspector = create<InspectorState>((set, get) => ({
  model: null,
  findings: [],
  loading: false,
  loadError: null,
  ruleSetId: "process",
  overrides: {},
  selectedId: null,
  query: "",
  tab: "overview",
  setTab: (tab) => set({ tab }),
  setQuery: (query) => set({ query }),
  select: (selectedId) => set({ selectedId }),
  setLoading: (loading) => set({ loading }),
  setLoadError: (loadError) => set({ loadError }),
  setReport: (model, findings, options) =>
    set(
      options?.keepPlace
        ? { model, findings, loadError: null }
        : { model, findings, selectedId: null, query: "", tab: "overview", loadError: null },
    ),
  setFindings: (findings) => set({ findings }),
  clear: () => set({ model: null, findings: [], selectedId: null, query: "", tab: "overview", loadError: null }),
  setRuleSet: (ruleSetId) => {
    set({ ruleSetId, overrides: {} });
    persist(ruleSetId, {});
    rerun();
  },
  toggleRule: (ruleId, enabled) => {
    const overrides = { ...get().overrides, [ruleId]: { ...get().overrides[ruleId], enabled } };
    set({ overrides });
    persist(get().ruleSetId, overrides);
    rerun();
  },
  setSeverity: (ruleId, severity) => {
    const overrides = { ...get().overrides, [ruleId]: { ...get().overrides[ruleId], severity } };
    set({ overrides });
    persist(get().ruleSetId, overrides);
    rerun();
  },
  setCandidate: (id, status) => {
    void import("./client").then(({ reviewCandidate }) => reviewCandidate(id, status));
  },
  confirmHigh: () => {
    void import("./client").then(({ confirmHighCandidates }) => confirmHighCandidates());
  },
  hydrate: () => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw) as PersistedRules;
      if (!RULE_SETS.some((set) => set.id === parsed.ruleSetId)) return;
      set({ ruleSetId: parsed.ruleSetId, overrides: parsed.overrides ?? {} });
    } catch {
      // Ignore a corrupt preference and keep the process standard.
    }
  },
}));
