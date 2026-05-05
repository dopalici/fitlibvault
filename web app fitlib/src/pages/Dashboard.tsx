import React from 'react';
import { motion } from 'motion/react';
import { 
  Flame, 
  BookOpen, 
  Clock, 
  Award, 
  TrendingUp, 
  ChevronRight,
  Search,
  Bookmark,
  LogIn,
  LogOut,
  Loader2,
  Download,
  AlertCircle
} from 'lucide-react';
import { cn } from '../lib/utils';
import { DataImporter } from '../components/DataImporter';
import { auth } from '../lib/firebase';
import { GoogleAuthProvider, signInWithPopup, signOut, onAuthStateChanged, User } from 'firebase/auth';
import { useState, useEffect } from 'react';

interface UserProgress {
  completedNodes: string[];
  favorites: string[];
  studyStreak: number;
  totalReadingTime: number;
  lastActivity?: any;
}

interface AnalyticsData {
  totalNodes: number;
  completedNodes: number;
  completionRate: number;
  studyStreak: number;
  totalReadingTime: number;
  seriesProgress: {
    series: string;
    total: number;
    completed: number;
    percentage: number;
  }[];
}

interface RecentNode {
  id: string;
  title: string;
  category: string;
  readingTime: number;
  lastAccessed: string;
}

// Mock data for initial rendering
const LAST_VIEWED = [
  { id: '1', title: 'Hypertrophy Mechanisms', series: 'B', progress: 85, time: '2 hours ago' },
  { id: '2', title: 'Creatine Monohydrate', series: 'C', progress: 100, time: '1 day ago' },
  { id: '3', title: 'VO2 Max Thresholds', series: 'E', progress: 45, time: '3 days ago' },
];

const SERIES_STATS = [
  { label: 'Foundational (A)', completed: 34, total: 65, color: 'text-blue-500' },
  { label: 'Resistance (B)', completed: 21, total: 78, color: 'text-green-500' },
  { label: 'Nutrition (C)', completed: 45, total: 105, color: 'text-orange-500' },
];

export const Dashboard: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [userProgress, setUserProgress] = useState<UserProgress | null>(null);
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [recentNodes, setRecentNodes] = useState<RecentNode[]>([]);
  const [isLoadingData, setIsLoadingData] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  useEffect(() => {
    return onAuthStateChanged(auth, (user) => {
      setUser(user);
    });
  }, []);

  const handleLogin = async () => {
    if (isLoggingIn) return;
    setIsLoggingIn(true);
    const provider = new GoogleAuthProvider();
    try {
      await signInWithPopup(auth, provider);
    } catch (err) {
      if (err instanceof Error && !err.message.includes('auth/cancelled-popup-request')) {
        console.error("Login failed", err);
      }
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleLogout = () => signOut(auth);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10">
      <header className="mb-12 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold mb-2">Welcome back, {user?.displayName || 'Scholar'}</h1>
          <p className="text-slate-400">Your evidence-based training starts here.</p>
        </div>
        <div>
          {user ? (
            <button 
              onClick={handleLogout}
              className="flex items-center gap-2 px-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-sm font-bold text-slate-400 hover:text-white transition-all shadow-xl"
            >
              <LogOut className="w-4 h-4" />
              Sign Out
            </button>
          ) : (
            <button 
              onClick={handleLogin}
              disabled={isLoggingIn}
              className={cn(
                "flex items-center gap-2 px-4 py-2 bg-blue-600 rounded-xl text-sm font-bold text-white hover:bg-blue-700 transition-all shadow-xl shadow-blue-500/20",
                isLoggingIn && "opacity-50 cursor-not-allowed"
              )}
            >
              {isLoggingIn ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <LogIn className="w-4 h-4" />
              )}
              {isLoggingIn ? 'Connecting...' : 'Login with Google'}
            </button>
          )}
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* LEFT COLUMN: Continue Reading */}
        <div className="lg:col-span-3 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-blue-400" />
              Continue Reading
            </h2>
          </div>
          
          <div className="space-y-4">
            {LAST_VIEWED.map((node, index) => (
              <motion.div
                key={node.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="group p-4 bg-slate-900/50 border border-slate-800 rounded-xl hover:border-blue-500/50 transition-all cursor-pointer"
              >
                <div className="flex justify-between items-start mb-2">
                  <span className={cn(
                    "px-2 py-0.5 rounded text-[10px] font-bold",
                    node.series === 'B' ? 'bg-green-500/10 text-green-500' :
                    node.series === 'C' ? 'bg-orange-500/10 text-orange-500' :
                    'bg-blue-500/10 text-blue-500'
                  )}>
                    Series {node.series}
                  </span>
                  <span className="text-[10px] text-slate-500">{node.time}</span>
                </div>
                <h3 className="font-bold text-sm mb-3 group-hover:text-blue-400 transition-colors">{node.title}</h3>
                <div className="space-y-1.5">
                  <div className="flex justify-between text-[10px] text-slate-400">
                    <span>Progress</span>
                    <span>{node.progress}%</span>
                  </div>
                  <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: `${node.progress}%` }}
                      className="h-full bg-blue-500"
                    />
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* CENTER COLUMN: My Progress */}
        <div className="lg:col-span-6 space-y-8">
          <div className="grid grid-cols-2 gap-4">
            <div className="p-6 bg-gradient-to-br from-orange-500/20 to-orange-900/20 border border-orange-500/20 rounded-2xl relative overflow-hidden group">
              <div className="absolute -right-4 -bottom-4 opacity-10 group-hover:scale-110 transition-transform">
                <Flame className="w-24 h-24" />
              </div>
              <div className="relative z-10">
                <p className="text-orange-500 font-bold text-xs uppercase tracking-wider mb-2">Study Streak</p>
                <div className="flex items-center gap-2">
                  <Flame className="w-8 h-8 text-orange-500" />
                  <span className="text-4xl font-black text-white">15 Days</span>
                </div>
              </div>
            </div>
            
            <div className="p-6 bg-gradient-to-br from-blue-500/20 to-blue-900/20 border border-blue-500/20 rounded-2xl relative overflow-hidden group">
              <div className="absolute -right-4 -bottom-4 opacity-10 group-hover:scale-110 transition-transform">
                <Clock className="w-24 h-24" />
              </div>
              <div className="relative z-10">
                <p className="text-blue-400 font-bold text-xs uppercase tracking-wider mb-2">Reading Time</p>
                <div className="flex items-center gap-2">
                  <Clock className="w-8 h-8 text-blue-400" />
                  <span className="text-4xl font-black text-white">12h 34m</span>
                </div>
              </div>
            </div>
          </div>

          <div className="p-8 bg-slate-900/40 border border-slate-800 rounded-2xl">
            <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
              <TrendingUp className="w-6 h-6 text-green-400" />
              Curriculum Mastery
            </h2>
            <div className="space-y-6">
              {SERIES_STATS.map((stat, i) => (
                <div key={i} className="space-y-2">
                  <div className="flex justify-between items-end">
                    <span className="font-semibold text-sm">{stat.label}</span>
                    <span className="text-xs text-slate-400">
                      <span className={stat.color}>{stat.completed}</span> / {stat.total} nodes ({Math.round(stat.completed/stat.total * 100)}%)
                    </span>
                  </div>
                  <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: `${(stat.completed/stat.total) * 100}%` }}
                      className={cn("h-full", stat.color.replace('text', 'bg'))}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="aspect-square bg-slate-900/40 border border-slate-800 rounded-2xl flex flex-col items-center justify-center gap-3 grayscale hover:grayscale-0 transition-all group cursor-help">
                <Award className="w-8 h-8 text-yellow-500/50 group-hover:text-yellow-500 transition-colors" />
                <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Locked</span>
              </div>
            ))}
          </div>
        </div>

        {/* RIGHT COLUMN: Quick Actions */}
        <div className="lg:col-span-3 space-y-8">
          <div>
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Bookmark className="w-5 h-5 text-blue-400" />
              My Favorites
            </h2>
            <div className="space-y-3">
              {['Anabolic Window Myth', 'Fiber & Satiety', 'Training to Failure'].map((f, i) => (
                <div key={i} className="p-3 bg-slate-900/30 border border-slate-800 rounded-lg hover:bg-slate-800 transition-colors cursor-pointer flex justify-between items-center group">
                  <span className="text-sm font-medium">{f}</span>
                  <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-blue-400" />
                </div>
              ))}
            </div>
          </div>

          <div className="p-6 bg-blue-600 rounded-2xl text-white group cursor-pointer overflow-hidden relative">
            <div className="absolute right-0 top-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16 group-hover:scale-110 transition-transform" />
            <h3 className="font-bold relative z-10">Export Report</h3>
            <p className="text-xs text-blue-100 mb-4 opacity-80 relative z-10">Download your research progress for your coach or peers.</p>
            <button className="bg-white text-blue-600 px-4 py-2 rounded-lg text-xs font-bold relative z-10 hover:bg-blue-50 transition-colors">
              Download PDF
            </button>
          </div>
          
          <div className="p-6 bg-slate-900/80 border border-slate-800 rounded-2xl">
            <h3 className="font-bold mb-3 text-sm">Quick Search</h3>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input 
                type="text" 
                placeholder="Find research..."
                className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2 pl-10 pr-4 text-xs focus:border-blue-500 outline-none"
              />
            </div>
          </div>

          {user?.email === 'ozkanenesibrahim@gmail.com' && (
            <div className="mt-8">
              <DataImporter />
            </div>
          )}
        </div>

      </div>
    </div>
  );
};
