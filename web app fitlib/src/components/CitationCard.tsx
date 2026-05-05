import React from 'react';
import { Citation } from '../types';
import { ExternalLink, CheckCircle2, Star, ShieldCheck } from 'lucide-react';
import { cn } from '../lib/utils';

interface CitationCardProps {
  citation: Citation;
}

const TYPE_COLORS = {
  'Meta-Analysis': 'text-yellow-500 border-yellow-500/30 bg-yellow-500/5',
  'RCT': 'text-slate-400 border-slate-400/30 bg-slate-400/5',
  'Review': 'text-amber-700 border-amber-700/30 bg-amber-700/5',
  'Systematic Review': 'text-blue-500 border-blue-500/30 bg-blue-500/5',
};

const TYPE_ICONS = {
  'Meta-Analysis': '📄',
  'RCT': '🧪',
  'Review': '📚',
  'Systematic Review': '🔍',
};

export const CitationCard: React.FC<CitationCardProps> = ({ citation }) => {
  const quality = citation.qualityBreakdown || {
    studyDesign: 0,
    evidenceQuality: 0,
    biasRisk: 'Medium',
    automationValidated: false
  };

  const renderStars = (count: number) => {
    return Array.from({ length: 5 }).map((_, i) => (
      <Star
        key={i}
        className={cn(
          "w-3 h-3 transition-colors",
          i < count ? "fill-yellow-500 text-yellow-500" : "text-slate-600"
        )}
      />
    ));
  };

  return (
    <div className="group relative bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-all duration-300">
      <div className="flex justify-between items-start mb-4">
        <div className={cn(
          "px-3 py-1 rounded-full text-xs font-semibold border flex items-center gap-2",
          TYPE_COLORS[citation.type]
        )}>
          <span>{TYPE_ICONS[citation.type]}</span>
          {citation.type} ({Math.round(citation.credibilityScore * 100)}% Credibility)
          {quality.automationValidated && (
            <ShieldCheck className="w-3 h-3 text-green-500" />
          )}
        </div>
        <div className="flex gap-2">
          {citation.doi && (
            <a
              href={`https://doi.org/${citation.doi}`}
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 bg-slate-800 rounded-lg hover:bg-slate-700 transition-colors"
            >
              <ExternalLink className="w-4 h-4 text-slate-300" />
            </a>
          )}
        </div>
      </div>

      <div className="mb-4">
        <p className="text-xs text-slate-400 font-medium mb-1">
          {citation.author}, et al. ({citation.year})
        </p>
        <h4 className="text-sm font-bold text-slate-100 leading-snug group-hover:text-blue-400 transition-colors">
          "{citation.title}"
        </h4>
        <p className="text-xs text-slate-500 mt-2 italic">
          Journal: {citation.journal}
        </p>
      </div>

      <div className="space-y-3 pt-4 border-t border-slate-800">
        <h5 className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Quality Breakdown</h5>
        <div className="grid grid-cols-2 gap-4">
          <div className="flex flex-col gap-1">
            <span className="text-[10px] text-slate-400">Study Design</span>
            <div className="flex">{renderStars(quality.studyDesign)}</div>
          </div>
          <div className="flex flex-col gap-1">
            <span className="text-[10px] text-slate-400">Evidence Quality</span>
            <div className="flex">{renderStars(quality.evidenceQuality)}</div>
          </div>
          <div className="flex flex-col gap-1">
            <span className="text-[10px] text-slate-400">Bias Risk</span>
            <span className={cn(
              "text-[10px] font-bold flex items-center gap-1",
              quality.biasRisk === 'Low' ? "text-green-500" : "text-yellow-500"
            )}>
              {quality.biasRisk} {quality.biasRisk === 'Low' && <CheckCircle2 className="w-2 h-2" />}
            </span>
          </div>
          <div className="flex flex-col gap-1">
            <span className="text-[10px] text-slate-400">Automation</span>
            <span className={cn(
              "text-[10px] font-bold flex items-center gap-1",
              quality.automationValidated ? "text-green-500" : "text-slate-500"
            )}>
              {quality.automationValidated ? 'PASSED' : 'PENDING'} {quality.automationValidated && <CheckCircle2 className="w-2 h-2" />}
            </span>
          </div>
        </div>
      </div>

      {quality.automationValidated && (
        <div className="mt-4 pt-4 border-t border-slate-800/50 flex items-center gap-2 group/tooltip">
          <div className="w-1.5 h-1.5 rounded-full bg-green-500/50 animate-pulse" />
          <span className="text-[9px] text-slate-500 italic">
            95%+ accuracy automated validation seal
          </span>
        </div>
      )}
    </div>
  );
};
