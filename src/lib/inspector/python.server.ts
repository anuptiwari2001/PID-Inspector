import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import type { Finding, NormalizedModel } from "./types";

export interface LedgerResult {
  ok: boolean;
  model?: NormalizedModel;
  findings?: Finding[];
  message?: string;
}

function projectRoot() {
  const seeds = [process.cwd(), "/workspace"];
  for (const seed of seeds) {
    let dir = seed;
    for (let i = 0; i < 6; i += 1) {
      if (existsSync(path.join(dir, "ledger", "__main__.py"))) return dir;
      const parent = path.dirname(dir);
      if (parent === dir) break;
      dir = parent;
    }
  }
  throw new Error("The Python inspector is not available on this server.");
}

function pythonBins() {
  const chosen = process.env.LEDGER_PYTHON?.trim();
  if (chosen) return [chosen];
  return process.platform === "win32" ? ["python", "python3"] : ["python3", "python"];
}

function runWith(bins: string[], index: number, cwd: string, payload: unknown): Promise<LedgerResult> {
  return new Promise((resolve, reject) => {
    const child = spawn(bins[index], ["-m", "ledger"], { cwd, stdio: ["pipe", "pipe", "pipe"] });
    const out: Buffer[] = [];
    const err: Buffer[] = [];
    child.stdout.on("data", (chunk: Buffer) => out.push(chunk));
    child.stderr.on("data", (chunk: Buffer) => err.push(chunk));
    child.on("error", (error: NodeJS.ErrnoException) => {
      if (error.code === "ENOENT" && index + 1 < bins.length) {
        resolve(runWith(bins, index + 1, cwd, payload));
        return;
      }
      reject(error);
    });
    child.on("close", (code) => {
      const text = Buffer.concat(out).toString("utf8");
      if (code !== 0) {
        reject(new Error(Buffer.concat(err).toString("utf8").trim() || `Python exited ${code}`));
        return;
      }
      try {
        resolve(JSON.parse(text) as LedgerResult);
      } catch {
        reject(new Error("The Python inspector returned something that was not a report."));
      }
    });
    child.stdin.write(JSON.stringify(payload));
    child.stdin.end();
  });
}

export function runLedger(payload: unknown): Promise<LedgerResult> {
  return runWith(pythonBins(), 0, projectRoot(), payload);
}
