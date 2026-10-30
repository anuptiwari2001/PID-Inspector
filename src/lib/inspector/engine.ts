import { createServerFn } from "@tanstack/react-start";
import type { Finding, NormalizedModel } from "./types";
import type { RuleOverrides } from "./rules";

export interface LedgerRequest {
  op: "inspect" | "checks" | "candidate" | "confirm-high";
  fileName?: string;
  dataBase64?: string;
  model?: NormalizedModel;
  ruleSetId?: string;
  overrides?: RuleOverrides;
  candidateId?: string;
  status?: "unreviewed" | "confirmed" | "rejected";
}

export interface LedgerResult {
  ok: boolean;
  model?: NormalizedModel;
  findings?: Finding[];
  message?: string;
}

export const ledgerOp = createServerFn({ method: "POST" })
  .validator((data: LedgerRequest) => data)
  .handler(async ({ data }): Promise<LedgerResult> => {
    const { runLedger } = await import("./python.server");
    return runLedger(data);
  });
