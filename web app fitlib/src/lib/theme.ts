/**
 * Theme: warm-dark default, light mode optional, persisted to localStorage,
 * reactive to `prefers-color-scheme` only on first load.
 *
 * The toggle drives `<html data-theme="...">`. All colour decisions in
 * `index.css` are token-based, so flipping the attribute swaps the entire
 * surface in one go without component churn.
 */

import { useEffect, useSyncExternalStore } from 'react';

export type Theme = 'dark' | 'light';

const STORAGE_KEY = 'fitlib.theme.v1';
const CHANGE_EVENT = 'fitlib:theme-changed';

function detectSystemPreference(): Theme {
  if (typeof window === 'undefined') return 'dark';
  return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
}

function readStored(): Theme | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw === 'light' || raw === 'dark' ? raw : null;
  } catch {
    return null;
  }
}

function applyTheme(theme: Theme) {
  if (typeof document === 'undefined') return;
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
}

/** Initialise the theme as early as possible, before React paints. */
export function bootstrapTheme(): Theme {
  const stored = readStored();
  const initial: Theme = stored ?? detectSystemPreference();
  applyTheme(initial);
  return initial;
}

export function setTheme(theme: Theme) {
  applyTheme(theme);
  try {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, theme);
      window.dispatchEvent(new CustomEvent(CHANGE_EVENT, { detail: theme }));
    }
  } catch {
    /* ignore quota errors */
  }
}

export function getTheme(): Theme {
  if (typeof document === 'undefined') return 'dark';
  const attr = document.documentElement.dataset.theme;
  return attr === 'light' ? 'light' : 'dark';
}

export function useTheme(): [Theme, (theme: Theme) => void, () => void] {
  const subscribe = (cb: () => void) => {
    if (typeof window === 'undefined') return () => undefined;
    window.addEventListener(CHANGE_EVENT, cb);
    const onStorage = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY) cb();
    };
    window.addEventListener('storage', onStorage);
    return () => {
      window.removeEventListener(CHANGE_EVENT, cb);
      window.removeEventListener('storage', onStorage);
    };
  };
  const theme = useSyncExternalStore<Theme>(subscribe, getTheme, () => 'dark' as Theme);

  // First-mount safety: if `<html data-theme>` somehow isn't set, set it.
  useEffect(() => {
    if (typeof document !== 'undefined' && !document.documentElement.dataset.theme) {
      bootstrapTheme();
    }
  }, []);

  return [theme, setTheme, () => setTheme(theme === 'dark' ? 'light' : 'dark')];
}
