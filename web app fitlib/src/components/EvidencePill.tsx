import React from 'react';
import { cn } from '../lib/utils';
import type { EvidenceQuality } from '../lib/noteSchema';

const TONE: Record<EvidenceQuality, string> = {
  High: 'border-emerald-500/40 text-emerald-300 bg-emerald-500/5',
  Medium: 'border-amber-500/40 text-amber-300 bg-amber-500/5',
  Low: 'border-rose-500/40 text-rose-300 bg-rose-500/5',
  Unknown: 'border-slate-700 text-slate-400 bg-slate-900/40',
};

interface Props {
  quality: EvidenceQuality;
  note?: string;
  className?: string;
}

export const EvidencePill: React.FC<Props> = ({ quality, note, className }) => (
  <span
    className={cn(
      'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-[10px] font-bold uppercase tracking-widest',
      TONE[quality],
      className
    )}
    title={note ? `${quality} \u2014 ${note}` : quality}
  >
    <span className="w-1.5 h-1.5 rounded-full bg-current" />
    {quality}
  </span>
);
