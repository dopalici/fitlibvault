/**
 * Quartz-style explorer for the Library route.
 *
 * Folder tree organised by series (A → F → Other), each folder collapsible,
 * with an in-tree filter at the top that scopes by title / id substring.
 * Replaces the old flat sidebar list which became unusable around the
 * 700-node mark.
 *
 * Stays a presentational component — the parent owns selection state and
 * the search query so URL params can drive everything.
 */

import React, { useMemo, useState } from 'react';
import { ChevronRight, Folder, FolderOpen, Lock, Search } from 'lucide-react';
import type { NodeData } from '../types';
import { cn } from '../lib/utils';
import { seriesLabel, seriesTone } from '../lib/libraryStats';

interface Props {
  nodes: NodeData[];
  selectedNodeId: string | null;
  lockedNodeIds?: Set<string>;
  searchQuery: string;
  onSearchChange: (next: string) => void;
  activeSeries: string | null;
  onSeriesChange: (series: string | null) => void;
  onSelectNode: (nodeId: string) => void;
}

export const LibraryExplorer: React.FC<Props> = ({
  nodes,
  selectedNodeId,
  lockedNodeIds,
  searchQuery,
  onSearchChange,
  activeSeries,
  onSeriesChange,
  onSelectNode,
}) => {
  const grouped = useMemo(() => {
    const map = new Map<string, NodeData[]>();
    nodes.forEach((node) => {
      const series = node.series || 'Other';
      if (!map.has(series)) map.set(series, []);
      map.get(series)!.push(node);
    });
    map.forEach((list) => list.sort(naturalSort));
    return Array.from(map.entries()).sort(([a], [b]) => seriesOrder(a) - seriesOrder(b));
  }, [nodes]);

  const [expanded, setExpanded] = useState<Set<string>>(() => {
    if (activeSeries) return new Set([activeSeries]);
    // Default: expand the first series so the tree isn't a wall of folders.
    return new Set([grouped[0]?.[0]].filter(Boolean) as string[]);
  });

  // When a focused node lives in a collapsed series, auto-expand it so the
  // selection stays visible.
  React.useEffect(() => {
    if (!selectedNodeId) return;
    const node = nodes.find((n) => n.id === selectedNodeId);
    if (!node) return;
    setExpanded((prev) => {
      if (prev.has(node.series)) return prev;
      const next = new Set(prev);
      next.add(node.series);
      return next;
    });
  }, [selectedNodeId, nodes]);

  const toggleSeries = (series: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(series)) next.delete(series);
      else next.add(series);
      return next;
    });
  };

  return (
    <aside
      className="flex flex-col w-72 shrink-0 h-full"
      style={{
        borderRight: '1px solid var(--hairline)',
        background: 'var(--paper)',
      }}
    >
      <div className="px-5 pt-6 pb-4">
        <div className="flex items-center gap-2.5 mb-5">
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center font-black italic"
            style={{
              background: 'var(--accent)',
              color: 'var(--paper)',
            }}
          >
            F
          </div>
          <div className="leading-tight">
            <h1
              className="text-lg font-semibold tracking-tight"
              style={{ color: 'var(--ink-strong)' }}
            >
              FitLib
            </h1>
            <p
              className="font-mono text-[10px] uppercase tracking-widest"
              style={{ color: 'var(--ink-faint)' }}
            >
              Library
            </p>
          </div>
        </div>

        <div className="relative mb-4">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5"
            style={{ color: 'var(--ink-faint)' }}
          />
          <input
            type="text"
            placeholder="Filter notes…"
            className="w-full text-sm rounded-lg py-2 pl-9 pr-3 outline-none transition-colors"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            style={{
              background: 'var(--paper-raised)',
              color: 'var(--ink)',
              border: '1px solid var(--hairline)',
            }}
          />
        </div>

        {activeSeries && (
          <button
            onClick={() => onSeriesChange(null)}
            className="text-[10px] uppercase tracking-widest font-semibold inline-flex items-center gap-1 mb-3"
            style={{ color: 'var(--accent)' }}
          >
            ← Clear series filter ({activeSeries})
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-3 pb-4">
        {grouped.length === 0 && (
          <div
            className="px-3 py-8 text-center text-xs leading-relaxed"
            style={{ color: 'var(--ink-faint)' }}
          >
            No notes match this filter.
          </div>
        )}
        {grouped.map(([series, items]) => {
          const isOpen = expanded.has(series);
          const tone = seriesTone(series);
          const visible = activeSeries && activeSeries !== series ? false : true;
          if (!visible) return null;
          return (
            <div key={series} className="mb-2">
              <button
                onClick={() => toggleSeries(series)}
                className="w-full flex items-center justify-between px-2 py-1.5 rounded-md transition-colors hover:bg-[var(--paper-elevated)]"
                style={{ color: 'var(--ink)' }}
              >
                <span className="flex items-center gap-2 min-w-0">
                  <ChevronRight
                    className={cn(
                      'w-3 h-3 transition-transform shrink-0',
                      isOpen && 'rotate-90'
                    )}
                    style={{ color: 'var(--ink-faint)' }}
                  />
                  {isOpen ? (
                    <FolderOpen className={cn('w-3.5 h-3.5 shrink-0', tone.text)} />
                  ) : (
                    <Folder className={cn('w-3.5 h-3.5 shrink-0', tone.text)} />
                  )}
                  <span
                    className="text-sm font-medium truncate"
                    style={{ color: 'var(--ink-strong)' }}
                  >
                    {seriesLabel(series)}
                  </span>
                </span>
                <span
                  className="font-mono text-[10px] tabular-nums"
                  style={{ color: 'var(--ink-faint)' }}
                >
                  {items.length}
                </span>
              </button>

              {isOpen && (
                <ul className="mt-1 ml-4 pl-3" style={{ borderLeft: '1px solid var(--hairline)' }}>
                  {items.map((node) => {
                    const isSelected = node.id === selectedNodeId;
                    const isLocked = lockedNodeIds?.has(node.id) ?? false;
                    return (
                      <li key={node.id}>
                        <button
                          onClick={() => onSelectNode(node.id)}
                          className={cn(
                            'w-full text-left flex items-center justify-between gap-2 rounded-md px-2 py-1.5 text-sm leading-tight transition-colors group',
                            isSelected
                              ? 'font-medium'
                              : 'hover:bg-[var(--paper-elevated)]'
                          )}
                          style={{
                            background: isSelected ? 'var(--accent-soft)' : 'transparent',
                            color: isSelected ? 'var(--ink-strong)' : 'var(--ink)',
                          }}
                        >
                          <span className="flex items-center gap-2 min-w-0">
                            <span
                              className={cn(
                                'w-1 h-1 rounded-full shrink-0',
                                tone.dot
                              )}
                            />
                            <span className="truncate">{node.title}</span>
                          </span>
                          {isLocked && (
                            <Lock
                              className="w-3 h-3 shrink-0"
                              style={{ color: 'var(--accent)' }}
                            />
                          )}
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          );
        })}
      </div>
    </aside>
  );
};

function seriesOrder(series: string): number {
  const order = ['A', 'B', 'C', 'D', 'E', 'F'];
  const idx = order.indexOf(series);
  return idx === -1 ? 99 : idx;
}

function naturalSort(a: NodeData, b: NodeData): number {
  // "A2" should sort before "A10"; pure title compare doesn't do that.
  const idA = parseSortKey(a.id);
  const idB = parseSortKey(b.id);
  if (idA.prefix !== idB.prefix) {
    return idA.prefix < idB.prefix ? -1 : 1;
  }
  if (idA.num !== idB.num) return idA.num - idB.num;
  return a.title.localeCompare(b.title);
}

function parseSortKey(id: string): { prefix: string; num: number } {
  const m = id.match(/^([A-Z]+)(\d+)/i);
  if (!m) return { prefix: id, num: 0 };
  return { prefix: m[1].toUpperCase(), num: parseInt(m[2], 10) };
}
