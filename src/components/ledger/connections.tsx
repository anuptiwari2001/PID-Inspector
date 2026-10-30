import { buildGraph, collapseId, GRAPH_NODE_H, GRAPH_NODE_W } from "@/lib/inspector/graph";
import { endpointLabel } from "@/lib/inspector/format";
import { useInspector } from "@/lib/inspector/store";
import { useReport } from "./use-report";
import { Panel } from "./ui";

export function Connections() {
  const { model, byId } = useReport();
  const selectedId = useInspector((state) => state.selectedId);
  if (!model) return null;
  const layout = buildGraph(model);
  const highlight = selectedId ? collapseId(selectedId, byId) : null;

  return (
    <div className="grid gap-4">
      <Panel className="overflow-auto p-3">
        {layout.nodes.length ? (
          <svg width={layout.width} height={layout.height} role="img" aria-label="Connection graph" className="max-w-none">
            {layout.links.map((link) => {
              const from = layout.nodes.find((node) => node.id === link.from);
              const to = layout.nodes.find((node) => node.id === link.to);
              if (!from || !to) return null;
              const active = highlight === from.id || highlight === to.id;
              return (
                <path
                  key={`${link.from}-${link.to}`}
                  d={curve(from, to)}
                  fill="none"
                  className={active ? "stroke-oxide" : "stroke-line"}
                  strokeWidth={active ? 2 : 1.5}
                />
              );
            })}
            {layout.nodes.map((node) => {
              const selected = highlight === node.id;
              return (
                <g
                  key={node.id}
                  role="button"
                  tabIndex={0}
                  onClick={() => {
                    if (!node.missing) useInspector.getState().select(node.id);
                  }}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && !node.missing) useInspector.getState().select(node.id);
                  }}
                >
                  <title>{node.missing ? `${node.label} was not imported` : node.label}</title>
                  <rect
                    x={node.x}
                    y={node.y}
                    width={GRAPH_NODE_W}
                    height={GRAPH_NODE_H}
                    rx="8"
                    className={
                      node.missing
                        ? "fill-stamp-soft stroke-stamp"
                        : selected
                          ? "fill-oxide stroke-oxide"
                          : "fill-sheet stroke-line"
                    }
                    strokeDasharray={node.missing ? "4 3" : undefined}
                  />
                  <text
                    x={node.x + 12}
                    y={node.y + 24}
                    className={`font-mono text-sm ${selected ? "fill-oxide-ink" : node.missing ? "fill-stamp" : "fill-ink"}`}
                  >
                    {clip(node.label, 18)}
                  </text>
                  <text
                    x={node.x + 12}
                    y={node.y + 42}
                    className={`text-xs ${selected ? "fill-oxide-ink" : "fill-muted"}`}
                  >
                    {clip(node.sublabel, 22)}
                  </text>
                </g>
              );
            })}
          </svg>
        ) : (
          <p className="px-2 py-6 text-sm text-muted">
            No objects to connect. PDF candidates do not become tie-ins, and a file with no connection records
            stays empty here on purpose.
          </p>
        )}
      </Panel>
      <Panel>
        <ul>
          {model.edges.length ? (
            model.edges.map((edge) => (
              <li key={edge.id} className="border-b border-line px-4 py-3 text-sm last:border-b-0">
                <p className="font-mono">
                  <EndButton id={edge.fromId || edge.ownerId} label={endpointLabel(edge.fromId || edge.ownerId, byId)} />
                  <span className="px-2 text-muted">to</span>
                  <EndButton id={edge.toId} label={edge.toId ? endpointLabel(edge.toId, byId) : "unset"} />
                </p>
                <p className="mt-1 text-xs text-muted">{edge.sourcePath}</p>
              </li>
            ))
          ) : (
            <li className="px-4 py-4 text-sm text-muted">No connection records were imported.</li>
          )}
        </ul>
      </Panel>
    </div>
  );
}

function EndButton({ id, label }: { id: string; label: string }) {
  const known = useReport().byId.has(id);
  if (!known) return <span className="text-stamp">{label}</span>;
  return (
    <button type="button" className="underline decoration-line underline-offset-4" onClick={() => useInspector.getState().select(id)}>
      {label}
    </button>
  );
}

function curve(
  from: { x: number; y: number },
  to: { x: number; y: number },
) {
  const forward = from.x <= to.x;
  const x1 = from.x + (forward ? GRAPH_NODE_W : 0);
  const y1 = from.y + GRAPH_NODE_H / 2;
  const x2 = to.x + (forward ? 0 : GRAPH_NODE_W);
  const y2 = to.y + GRAPH_NODE_H / 2;
  const dir = x1 < x2 ? 1 : -1;
  const bend = Math.max(24, Math.abs(x2 - x1) / 2);
  return `M ${x1} ${y1} C ${x1 + dir * bend} ${y1}, ${x2 - dir * bend} ${y2}, ${x2} ${y2}`;
}

function clip(value: string, max: number) {
  return value.length > max ? `${value.slice(0, max - 1)}…` : value;
}
