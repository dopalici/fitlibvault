/**
 * Stack-aware note navigation (Andy Matuschak pattern).
 *
 * URL shape: /library?stack=A1-ENERGY-BALANCE,A2-BMR-TDEE,A3-MACRONUTRIENTS
 * Clicking a [[wikilink]] inside note N pushes the target onto the stack
 * after N. Browser back/forward Just Works because each push is a
 * history.pushState.
 *
 * Limits: a "max columns visible" parameter (default 3) controls how many
 * columns the reader renders at once; the rest scroll horizontally.
 */

import { useCallback, useEffect, useMemo, useState } from 'react';

const STACK_PARAM = 'stack';

function readStackFromLocation(): string[] {
  if (typeof window === 'undefined') return [];
  const params = new URLSearchParams(window.location.search);
  const raw = params.get(STACK_PARAM);
  if (!raw) return [];
  return raw.split(',').map((id) => id.trim()).filter(Boolean);
}

function writeStackToLocation(stack: string[], replace = false) {
  if (typeof window === 'undefined') return;
  const params = new URLSearchParams(window.location.search);
  if (stack.length === 0) {
    params.delete(STACK_PARAM);
  } else {
    params.set(STACK_PARAM, stack.join(','));
  }
  const search = params.toString();
  const url = `${window.location.pathname}${search ? `?${search}` : ''}${window.location.hash}`;
  if (replace) {
    window.history.replaceState({ stack }, '', url);
  } else {
    window.history.pushState({ stack }, '', url);
  }
}

export interface UseNoteStackResult {
  stack: string[];
  /** Push a new note immediately after `fromId`. Truncates anything to its right. */
  pushAfter: (fromId: string | null, nextId: string) => void;
  /** Open a single-note view, replacing the stack. */
  open: (id: string) => void;
  /** Close one note (and everything to its right). */
  closeFrom: (id: string) => void;
  /** Reset to empty (close all). */
  closeAll: () => void;
}

export function useNoteStack(): UseNoteStackResult {
  const [stack, setStack] = useState<string[]>(() => readStackFromLocation());

  useEffect(() => {
    const onPop = () => setStack(readStackFromLocation());
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);

  const commit = useCallback((next: string[], replace = false) => {
    setStack(next);
    writeStackToLocation(next, replace);
  }, []);

  const pushAfter = useCallback((fromId: string | null, nextId: string) => {
    setStack((current) => {
      // Already open? Just scroll to it (caller handles scroll).
      if (current.includes(nextId)) {
        return current;
      }
      if (fromId === null) {
        const next = [nextId];
        writeStackToLocation(next);
        return next;
      }
      const idx = current.indexOf(fromId);
      const base = idx >= 0 ? current.slice(0, idx + 1) : current;
      const next = [...base, nextId];
      writeStackToLocation(next);
      return next;
    });
  }, []);

  const open = useCallback((id: string) => commit([id]), [commit]);

  const closeFrom = useCallback((id: string) => {
    setStack((current) => {
      const idx = current.indexOf(id);
      if (idx < 0) return current;
      const next = current.slice(0, idx);
      writeStackToLocation(next);
      return next;
    });
  }, []);

  const closeAll = useCallback(() => commit([]), [commit]);

  return useMemo(
    () => ({ stack, pushAfter, open, closeFrom, closeAll }),
    [stack, pushAfter, open, closeFrom, closeAll]
  );
}
