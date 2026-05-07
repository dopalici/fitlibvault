/**
 * Local-first favourites for notes.
 *
 * Same rationale as `recentlyViewed.ts`: the reader is the hot path and we
 * don't want a Firestore round-trip on every star click. The Dashboard reads
 * from this store; if a real account is ever added, the same shape can sync
 * up to a remote document without touching the call sites.
 *
 * Subscribers can listen for the `'fitlib:favorites-changed'` window event
 * to live-update without polling.
 */

const STORAGE_KEY = 'fitlib.favorites.v1';
const CHANGE_EVENT = 'fitlib:favorites-changed';

export interface FavoriteEntry {
  id: string;
  title: string;
  series: string;
  /** Time the user starred the note (ms epoch). */
  addedAt: number;
}

function safeRead(): FavoriteEntry[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as FavoriteEntry[];
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((e) => e && typeof e.id === 'string');
  } catch {
    return [];
  }
}

function safeWrite(entries: FavoriteEntry[]): void {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
    window.dispatchEvent(new CustomEvent(CHANGE_EVENT));
  } catch {
    /* quota exceeded — drop the write silently */
  }
}

export function getFavorites(): FavoriteEntry[] {
  return safeRead().sort((a, b) => b.addedAt - a.addedAt);
}

export function isFavorite(nodeId: string): boolean {
  return safeRead().some((e) => e.id === nodeId);
}

export function toggleFavorite(node: { id: string; title: string; series: string }): boolean {
  const current = safeRead();
  const exists = current.some((e) => e.id === node.id);
  const next = exists
    ? current.filter((e) => e.id !== node.id)
    : [
        { id: node.id, title: node.title, series: node.series, addedAt: Date.now() },
        ...current,
      ];
  safeWrite(next);
  return !exists;
}

export function subscribeFavorites(listener: () => void): () => void {
  if (typeof window === 'undefined') return () => undefined;
  const wrapped = () => listener();
  window.addEventListener(CHANGE_EVENT, wrapped);
  // Cross-tab updates.
  const onStorage = (e: StorageEvent) => {
    if (e.key === STORAGE_KEY) listener();
  };
  window.addEventListener('storage', onStorage);
  return () => {
    window.removeEventListener(CHANGE_EVENT, wrapped);
    window.removeEventListener('storage', onStorage);
  };
}
