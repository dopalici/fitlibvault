/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Library } from './pages/Library';
import { Dashboard } from './pages/Dashboard';
import { About } from './pages/About';
import { Landing } from './pages/Landing';
import { cn } from './lib/utils';
import { LayoutDashboard, Library as LibraryIcon, Info, Home } from 'lucide-react';

function Navigation() {
  const location = useLocation();

  const navItems = [
    { path: '/library', label: 'Library', icon: LibraryIcon },
    { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/about', label: 'Transparency', icon: Info },
  ];

  return (
    <nav className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-slate-900/80 backdrop-blur-xl border border-slate-800 px-2 py-2 rounded-2xl flex items-center gap-1 z-[100] shadow-2xl">
      {navItems.map((item) => {
        const isActive = location.pathname === item.path;
        return (
          <Link
            key={item.path}
            to={item.path}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all",
              isActive 
                ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20" 
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
            )}
          >
            <item.icon className="w-4 h-4" />
            <span className="hidden md:inline">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}

export default function App() {
  return (
    <Router>
      <main className="relative min-h-screen bg-slate-950">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/library" element={<Library />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/about" element={<About />} />
        </Routes>
        <Navigation />
      </main>
    </Router>
  );
}

