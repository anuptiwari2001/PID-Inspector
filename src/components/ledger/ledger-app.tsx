import { useEffect } from "react";
import { useInspector } from "@/lib/inspector/store";
import { Intake } from "./intake";
import { ReportView } from "./report-view";

export function LedgerApp() {
  const model = useInspector((state) => state.model);
  const hydrate = useInspector((state) => state.hydrate);
  useEffect(() => {
    hydrate();
  }, [hydrate]);

  return (
    <div className="min-h-screen">
      <div className="sticky top-0 z-20">
        <div className="h-1.5 bg-oxide" />
        <header className="border-b border-line bg-sheet">
          <div className="mx-auto flex h-14 max-w-6xl items-center gap-3 px-4">
            <span className="grid size-8 place-items-center rounded-lg bg-oxide font-mono text-sm text-oxide-ink">
              Ld
            </span>
            <div className="min-w-0">
              <p className="text-sm leading-none font-medium">Ledger</p>
              <p className="mt-1 text-xs text-muted">P&ID quality report</p>
            </div>
          </div>
        </header>
      </div>
      <main className="mx-auto max-w-6xl px-4 py-6">{model ? <ReportView /> : <Intake />}</main>
    </div>
  );
}
