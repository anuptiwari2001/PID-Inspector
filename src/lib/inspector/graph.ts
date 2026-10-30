import type { EngObject, NormalizedModel, ObjectKind } from "./types";
import { inCheckSet } from "./types";

export interface GraphNode {
  id: string;
  label: string;
  sublabel: string;
  kind: ObjectKind | "missing";
  x: number;
  y: number;
  missing: boolean;
}

export interface GraphLink {
  from: string;
  to: string;
}

export interface GraphLayout {
  nodes: GraphNode[];
  links: GraphLink[];
  width: number;
  height: number;
}

const NODE_W = 176;
const NODE_H = 56;
const GAP_X = 56;
const GAP_Y = 16;

export function collapseId(id: string, byId: Map<string, EngObject>): string {
  const obj = byId.get(id);
  if (!obj) return id;
  if (obj.kind === "nozzle" && obj.parentId && byId.has(obj.parentId)) return obj.parentId;
  if (obj.objectType === "PipingNetworkSegment" && obj.parentId) {
    const parent = byId.get(obj.parentId);
    if (parent?.objectType === "PipingNetworkSystem") return parent.id;
  }
  return obj.id;
}

export function buildGraph(model: NormalizedModel): GraphLayout {
  const visible = model.objects.filter(inCheckSet);
  const byId = new Map(visible.map((obj) => [obj.id, obj]));
  const linkKeys = new Set<string>();
  const links: GraphLink[] = [];
  const referenced = new Set<string>();

  for (const edge of model.edges) {
    const raw = [edge.ownerId, edge.fromId, edge.toId].filter(Boolean);
    const ids = [...new Set(raw.map((id) => collapseId(id, byId)))];
    for (let i = 0; i < ids.length; i += 1) {
      for (let j = i + 1; j < ids.length; j += 1) {
        const a = ids[i];
        const b = ids[j];
        if (a === b) continue;
        const key = [a, b].sort().join("|");
        if (linkKeys.has(key)) continue;
        linkKeys.add(key);
        links.push({ from: a, to: b });
        referenced.add(a);
        referenced.add(b);
      }
    }
  }

  const nodeIds = new Set<string>(referenced);
  for (const obj of visible) {
    if (obj.kind === "nozzle") continue;
    if (obj.objectType === "PipingNetworkSegment" && obj.parentId && byId.has(obj.parentId)) continue;
    if (obj.kind === "equipment" || obj.kind === "valve" || obj.kind === "instrument" || obj.kind === "piping") {
      nodeIds.add(obj.id);
    }
  }

  const nodes: GraphNode[] = [...nodeIds].map((id) => {
    const obj = byId.get(id);
    if (!obj) {
      return {
        id,
        label: id,
        sublabel: "not imported",
        kind: "missing",
        x: 0,
        y: 0,
        missing: true,
      };
    }
    return {
      id,
      label: obj.tag ?? "missing",
      sublabel: obj.objectType.trim() || obj.kind,
      kind: obj.kind,
      x: 0,
      y: 0,
      missing: false,
    };
  });

  const adjacency = new Map<string, string[]>();
  for (const node of nodes) adjacency.set(node.id, []);
  for (const link of links) {
    adjacency.get(link.from)?.push(link.to);
    adjacency.get(link.to)?.push(link.from);
  }

  const depth = new Map<string, number>();
  const queue: string[] = [];
  for (const node of nodes) {
    if (node.kind === "equipment") {
      depth.set(node.id, 0);
      queue.push(node.id);
    }
  }
  if (!queue.length && nodes.length) {
    depth.set(nodes[0].id, 0);
    queue.push(nodes[0].id);
  }
  while (queue.length) {
    const current = queue.shift()!;
    const nextDepth = (depth.get(current) ?? 0) + 1;
    for (const neighbor of adjacency.get(current) ?? []) {
      if (depth.has(neighbor)) continue;
      depth.set(neighbor, nextDepth);
      queue.push(neighbor);
    }
  }
  let maxDepth = 0;
  for (const value of depth.values()) maxDepth = Math.max(maxDepth, value);
  const fallback = depth.size ? maxDepth + 1 : 0;
  for (const node of nodes) {
    if (!depth.has(node.id)) depth.set(node.id, fallback);
  }

  const layers = new Map<number, GraphNode[]>();
  for (const node of nodes) {
    const layer = depth.get(node.id) ?? 0;
    const list = layers.get(layer) ?? [];
    list.push(node);
    layers.set(layer, list);
  }
  const kindRank: Record<string, number> = {
    equipment: 0,
    valve: 1,
    piping: 2,
    instrument: 3,
    other: 4,
    nozzle: 5,
    missing: 6,
  };
  let height = 80;
  const layerIndexes = [...layers.keys()].sort((a, b) => a - b);
  for (const layer of layerIndexes) {
    const list = layers.get(layer) ?? [];
    list.sort(
      (a, b) => kindRank[a.kind] - kindRank[b.kind] || a.label.localeCompare(b.label),
    );
    list.forEach((node, index) => {
      node.x = 20 + layer * (NODE_W + GAP_X);
      node.y = 20 + index * (NODE_H + GAP_Y);
    });
    height = Math.max(height, 20 + list.length * (NODE_H + GAP_Y) + 12);
  }
  const width = 40 + Math.max(1, layerIndexes.length) * (NODE_W + GAP_X);
  return { nodes, links, width, height };
}

export const GRAPH_NODE_W = NODE_W;
export const GRAPH_NODE_H = NODE_H;
