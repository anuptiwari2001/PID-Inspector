import { kindLabel } from "@/lib/inspector/format";
import { useInspector } from "@/lib/inspector/store";
import { useReport } from "./use-report";
import { Panel } from "./ui";

export function Candidates() {
  const { model } = useReport();
  const setCandidate = useInspector((state) => state.setCandidate);
  const confirmHigh = useInspector((state) => state.confirmHigh);
  if (!model) return null;
  const pending = model.candidates.filter((candidate) => candidate.status === "unreviewed");

  return (
    <div className="grid gap-4">
      <Panel className="px-4 py-4">
        <h2 className="font-medium">Designer review</h2>
        <p className="mt-1 text-sm text-muted">
          These tags were read from a text layer. Confirming one adds it to the same check set as a Proteus
          object. It does not create a connection, and it does not prove the symbol.
        </p>
        <button
          type="button"
          disabled={!pending.some((candidate) => candidate.confidence >= 0.85)}
          onClick={() => confirmHigh()}
          className="mt-3 inline-flex h-11 items-center rounded-lg bg-oxide px-4 font-medium text-oxide-ink disabled:opacity-50"
        >
          Confirm 85% and above
        </button>
      </Panel>
      {model.transcript.length ? (
        <Panel className="px-4 py-4">
          <h2 className="font-medium">Text layer</h2>
          <ol className="mt-2 grid gap-1 font-mono text-sm">
            {model.transcript.map((line, index) => (
              <li key={`${line.page}-${index}`}>
                <span className="text-muted">p{line.page} </span>
                {line.text}
              </li>
            ))}
          </ol>
        </Panel>
      ) : null}
      <ul className="grid gap-3">
        {model.candidates.map((candidate) => (
          <li key={candidate.id} className="rounded-xl border border-line bg-sheet px-4 py-3">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <p className="font-mono text-lg">{candidate.suggestedTag}</p>
              <p className="font-mono text-xs text-muted">{Math.round(candidate.confidence * 100)}% confidence</p>
            </div>
            <p className="text-sm">
              {kindLabel(candidate.suggestedKind)}
              {candidate.suggestedType ? ` · ${candidate.suggestedType}` : " · class not available in extracted text"}
            </p>
            <p className="mt-1 text-sm text-muted">{candidate.context}</p>
            <p className="mt-1 text-xs text-muted">{candidate.location}</p>
            {candidate.hint ? <p className="mt-2 text-sm">{candidate.hint}</p> : null}
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => setCandidate(candidate.id, candidate.status === "confirmed" ? "unreviewed" : "confirmed")}
                className={`inline-flex h-11 items-center rounded-lg px-3 text-sm font-medium ${candidate.status === "confirmed" ? "bg-oxide text-oxide-ink" : "border border-line bg-sheet"}`}
              >
                {candidate.status === "confirmed" ? "Confirmed" : "Confirm"}
              </button>
              <button
                type="button"
                onClick={() => setCandidate(candidate.id, candidate.status === "rejected" ? "unreviewed" : "rejected")}
                className={`inline-flex h-11 items-center rounded-lg border px-3 text-sm ${candidate.status === "rejected" ? "border-stamp text-stamp" : "border-line"}`}
              >
                {candidate.status === "rejected" ? "Rejected" : "Reject"}
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
