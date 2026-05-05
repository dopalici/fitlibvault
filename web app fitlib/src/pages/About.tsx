import React from 'react';
import { motion } from 'motion/react';
import { 
  ShieldCheck, 
  Zap, 
  Search, 
  BarChart3, 
  CheckCircle2, 
  ArrowRight,
  Database,
  Cpu,
  RefreshCcw,
  Network
} from 'lucide-react';

const METRICS = [
  { label: 'Citation Accuracy', value: '95.4%', trend: 'up' },
  { label: 'Processing Speed', value: '10.2x', trend: 'vs manual' },
  { label: 'System Uptime', value: '99.9%', trend: 'stable' },
  { label: 'Papers Analyzed', value: '50,000+', trend: 'global' },
];

export const About: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 selection:bg-blue-500/30">
      {/* HERO */}
      <section className="relative py-24 px-6 overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-blue-500/10 via-transparent to-transparent pointer-events-none" />
        
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 px-3 py-1 bg-blue-500/10 border border-blue-500/20 rounded-full text-blue-400 text-xs font-bold mb-8 uppercase tracking-widest"
          >
            <ShieldCheck className="w-3 h-3" />
            Enterprise-Grade Research Automation
          </motion.div>
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-4xl md:text-6xl font-black mb-6 bg-gradient-to-b from-white to-slate-400 bg-clip-text text-transparent"
          >
            Science at the Speed of Software.
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-lg md:text-xl text-slate-400 mb-12 max-w-2xl mx-auto leading-relaxed"
          >
            How we use multi-layered automation to manage 2000+ fitness topics with 95%+ citation accuracy.
          </motion.p>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto">
            {METRICS.map((m, i) => (
              <motion.div
                key={m.label}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.3 + i * 0.1 }}
                className="p-4 bg-slate-900/50 border border-slate-800 rounded-2xl backdrop-blur-sm"
              >
                <div className="text-2xl font-black text-white mb-1">{m.value}</div>
                <div className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">{m.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* PROBLEM & SOLUTION */}
      <section className="py-24 px-6 bg-slate-900/20">
        <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-16 items-center">
          <div>
            <h2 className="text-3xl font-bold mb-6">The Legacy Problem</h2>
            <p className="text-slate-400 mb-8 text-lg leading-relaxed">
              Manual citation management is slow, error-prone, and unsustainable for large fitness libraries. Human reviewers often miss bias, incorrectly classify study designs, or fail to keep up with the 3,000+ new papers published daily.
            </p>
            <ul className="space-y-4">
              {[
                'Information Decay: Data becomes obsolete in 18-24 months.',
                'Observer Bias: Subjective interpretation of evidence quality.',
                'Volume Paralysis: Impossible to track 2000+ topics manually.',
              ].map((item, i) => (
                <li key={i} className="flex items-start gap-3 text-slate-300">
                  <div className="mt-1.5 w-1.5 h-1.5 rounded-full bg-red-500 shrink-0" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
          
          <div className="relative">
            <div className="absolute inset-0 bg-blue-500/10 blur-3xl rounded-full" />
            <div className="relative p-8 bg-slate-900 border border-slate-800 rounded-3xl space-y-8">
              <h3 className="text-xl font-bold flex items-center gap-2">
                <Zap className="w-5 h-5 text-blue-400" />
                The FitLib Solution
              </h3>
              
              <div className="space-y-6">
                {[
                  { icon: Search, title: 'Multi-API Discovery', desc: 'Auto-scanning PubMed, CrossRef, and Semantic Scholar.' },
                  { icon: BarChart3, title: 'AI Quality Scoring', desc: 'ML models classify study design and evidence strength.' },
                  { icon: ShieldCheck, title: 'GRADE Assessment', desc: 'Automated evidence grading based on standardized criteria.' },
                  { icon: RefreshCcw, title: 'Real-time Sync', desc: 'Content updates automatically when new evidence emerges.' }
                ].map((step, i) => (
                  <div key={i} className="flex gap-4 group">
                    <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center shrink-0 group-hover:bg-blue-600 transition-colors">
                      <step.icon className="w-5 h-5 text-blue-400 group-hover:text-white" />
                    </div>
                    <div>
                      <h4 className="font-bold text-slate-200 text-sm">{step.title}</h4>
                      <p className="text-xs text-slate-500">{step.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* WORKFLOW DIAGRAM SIMULATION */}
      <section className="py-24 px-6 overflow-hidden">
        <div className="max-w-6xl mx-auto text-center mb-16">
          <h2 className="text-3xl font-bold mb-4">Automation Quality Gates</h2>
          <p className="text-slate-400">Our 5-stage validation process ensures academic rigor.</p>
        </div>
        
        <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-5 gap-4 relative">
          <div className="hidden md:block absolute top-1/2 left-0 w-full h-[2px] bg-slate-800 -translate-y-1/2 z-0" />
          
          {[
            { icon: Database, label: 'Ingestion' },
            { icon: Network, label: 'Classification' },
            { icon: Cpu, label: 'Scoring' },
            { icon: ShieldCheck, label: 'Validation' },
            { icon: CheckCircle2, label: 'Deployment' },
          ].map((node, i) => (
            <div key={i} className="relative z-10 flex flex-col items-center gap-4">
              <div className="w-16 h-16 rounded-full bg-slate-900 border-2 border-slate-800 flex items-center justify-center hover:border-blue-500 transition-all group">
                <node.icon className="w-8 h-8 text-slate-600 group-hover:text-blue-400" />
              </div>
              <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">{node.label}</span>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6 bg-blue-600">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-5xl font-black text-white mb-8">Trust but Verify.</h2>
          <p className="text-blue-100 text-lg mb-12 opacity-90 max-w-xl mx-auto">
            Our automation tools are open for inspection. We believe transparency is the foundation of evidence-based practice.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button className="bg-white text-blue-600 px-8 py-4 rounded-full font-bold hover:bg-blue-50 transition-all flex items-center justify-center gap-2">
              View Toolset on GitHub <ArrowRight className="w-4 h-4" />
            </button>
            <button className="bg-blue-700 text-white border border-blue-500 px-8 py-4 rounded-full font-bold hover:bg-blue-800 transition-all">
              Technical Documentation
            </button>
          </div>
        </div>
      </section>

      <footer className="py-12 border-t border-slate-900 text-center">
        <p className="text-slate-600 text-sm">Powered by PubMed, CrossRef, & Semantic Scholar Knowledge Graph.</p>
      </footer>
    </div>
  );
};
