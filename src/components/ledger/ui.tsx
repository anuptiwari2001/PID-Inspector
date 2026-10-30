import type { ReactNode } from "react";
import type { Severity } from "@/lib/inspector/types";
import { severityLabel } from "@/lib/inspector/format";

export function SeverityChip({ severity }: { severity: Severity }) {
  const tone =
    severity === "error"
      ? "bg-stamp-soft text-stamp"
      : severity === "warning"
        ? "border border-line bg-paper text-ink"
        : severity === "review"
          ? "bg-oxide-soft text-oxide"
          : "bg-paper text-muted";
  return (
    <span className={`inline-flex h-6 shrink-0 items-center rounded-md px-2 font-mono text-xs ${tone}`}>
      {severityLabel(severity)}
    </span>
  );
}

export function Meta({ children }: { children: string }) {
  return <p className="font-mono text-xs tracking-wide text-muted uppercase">{children}</p>;
}

export function Panel({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`rounded-xl border border-line bg-sheet ${className}`}>{children}</section>;
}
