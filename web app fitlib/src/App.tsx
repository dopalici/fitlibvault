/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { cn } from './lib/utils';
import { Moon, Sun } from 'lucide-react';
import { useTheme } from './lib/theme';

const Landing = lazy(() => import('./pages/Landing').then((m) => ({ default: m.Landing })));
const Library = lazy(() => import('./pages/Library').then((m) => ({ default: m.Library })));
const Dashboard = lazy(() => import('./pages/Dashboard').then((m) => ({ default: m.Dashboard })));
const About = lazy(() => import('./pages/About').then((m) => ({ default: m.About })));

function TopBar() {
  const location = useLocation();
  const [theme, , toggleTheme] = useTheme();

  // Landing pages get to own their own chrome — the breadcrumb bar is for the
  // working surfaces (Library / Dashboard / Transparency).
  if (location.pathname === '/') return null;

  const navItems = [
    { path: '/library', label: 'Library' },
    { path: '/dashboard', label: 'Dashboard' },
    { path: '/about', label: 'Transparency' },
  ];

  return (
    <header
      className="sticky top-0 z-50 h-12 flex items-center justify-between px-6"
      style={{
        background: 'color-mix(in oklab, var(--paper) 92%, transparent)',
        borderBottom: '1px solid var(--hairline)',
        backdropFilter: 'blur(8px)',
      }}
    >
      <div className="flex items-center gap-2 min-w-0">
        <Link
          to="/"
          className="flex items-center gap-2 shrink-0"
          aria-label="FitLib home"
        >
          <span
            className="w-6 h-6 rounded-md flex items-center justify-center font-black italic text-[11px]"
            style={{ background: 'var(--accent)', color: 'var(--paper)' }}
          >
            F
          </span>
          <span
            className="text-sm font-semibold tracking-tight"
            style={{ color: 'var(--ink-strong)' }}
          >
            FitLib
          </span>
        </Link>
        <span style={{ color: 'var(--ink-faint)' }}>/</span>
        <nav className="flex items-center gap-1 min-w-0 overflow-x-auto">
          {navItems.map((item) => {
            const isActive = location.pathname.startsWith(item.path);
            return (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  'px-2.5 py-1 rounded-md text-sm transition-colors whitespace-nowrap',
                  isActive ? 'font-semibold' : 'hover:bg-[var(--paper-elevated)]'
                )}
                style={{
                  color: isActive ? 'var(--ink-strong)' : 'var(--ink-muted)',
                }}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => toggleTheme()}
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
          className="p-2 rounded-md transition-colors hover:bg-[var(--paper-elevated)]"
          style={{ color: 'var(--ink-muted)' }}
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
        >
          {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <Router>
      <main
        className="relative min-h-screen flex flex-col"
        style={{ background: 'var(--paper)' }}
      >
        <TopBar />
        <div className="flex-1 min-h-0 flex flex-col">
          <Suspense fallback={<div className="flex-1" aria-hidden style={{ background: 'var(--paper)' }} />}>
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/library" element={<Library />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/about" element={<About />} />
            </Routes>
          </Suspense>
        </div>
      </main>
    </Router>
  );
}
