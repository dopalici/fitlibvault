/**
 * Backlinks index.
 *
 * Quartz / Andy Matuschak / Obsidian all close the loop the same way:
 * forward [[wikilinks]] in the prose plus a reverse "Linked from" panel at
 * the bottom of every page. Given an array of nodes, this helper computes
 * the reverse graph once and serves O(1) lookups for the sidekick rail.
 *
 * We also expose a `localGraph` builder that returns the immediate
 * neighbourhood of a node (1-hop forward + reverse) so the right-rail
 * graphlet has a tight, contextual subset to render rather than the full
 * 700-node firmament.
 */

import type { NodeData, NodeSummary } from '../types';

export interface BacklinkEntry {
  /** The id of the note that links *to* the focused node. */
  id: string;
  title: string;
  series: string;
}

export type BacklinkIndex = Map<string, BacklinkEntry[]>;

type Linkable = Pick<NodeData | NodeSummary, 'id' | 'title' | 'series' | 'links'>;

export function buildBacklinkIndex(nodes: Linkable[]): BacklinkIndex {
  const index: BacklinkIndex = new Map();
  const byId = new Map<string, Linkable>();
  nodes.forEach((n) => byId.set(n.id, n));

  nodes.forEach((source) => {
    (source.links || []).forEach((targetId) => {
      if (targetId === source.id) return;
      if (!byId.has(targetId)) return;
      const list = index.get(targetId) || [];
      // Dedupe — in case a source links the same target twice.
      if (!list.some((entry) => entry.id === source.id)) {
        list.push({ id: source.id, title: source.title, series: source.series });
      }
      index.set(targetId, list);
    });
  });

  return index;
}

export interface LocalGraphSlice {
  nodes: { id: string; title: string; series: string }[];
  links: { source: string; target: string }[];
}

/**
 * Returns the focused node plus 1-hop forward links and 1-hop backlinks,
 * deduped, capped to `maxNodes` for visual sanity.
 */
export function buildLocalGraph(
  nodes: Linkable[],
  focusId: string,
  backlinks: BacklinkIndex,
  maxNodes = 18
): LocalGraphSlice {
  const byId = new Map<string, Linkable>();
  nodes.forEach((n) => byId.set(n.id, n));
  const focus = byId.get(focusId);
  if (!focus) return { nodes: [], links: [] };

  const ids = new Set<string>([focusId]);
  (focus.links || []).slice(0, maxNodes).forEach((id) => byId.has(id) && ids.add(id));
  (backlinks.get(focusId) || []).slice(0, maxNodes).forEach((entry) => ids.add(entry.id));

  const sliceNodes = Array.from(ids)
    .slice(0, maxNodes + 1)
    .map((id) => {
      const n = byId.get(id)!;
      return { id: n.id, title: n.title, series: n.series };
    });

  const sliceIds = new Set(sliceNodes.map((n) => n.id));
  const links: { source: string; target: string }[] = [];
  sliceNodes.forEach((n) => {
    const source = byId.get(n.id)!;
    (source.links || []).forEach((targetId) => {
      if (sliceIds.has(targetId)) {
        links.push({ source: n.id, target: targetId });
      }
    });
  });

  return { nodes: sliceNodes, links };
}
