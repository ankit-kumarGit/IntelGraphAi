import React, { useState } from 'react';
import { AlertTriangle, Info, ShieldCheck, X } from 'lucide-react';

export default function SafetyDisclaimer() {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-amber-950/25 border-b border-amber-900/30 px-4 py-1.5 text-xs text-amber-300/90 flex items-center justify-between transition-all select-none">
      <div className="flex items-center gap-2 overflow-hidden">
        <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
        <span className="truncate text-xs">
          <strong>⚠ AI decision support</strong> — verify against approved procedures before work.
        </span>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-[11px] underline text-amber-400 hover:text-amber-200 font-medium ml-1 shrink-0"
        >
          {expanded ? 'Hide Details' : 'Details'}
        </button>
      </div>

      <div className="hidden sm:flex items-center gap-2 text-[11px] text-amber-400/80 font-mono shrink-0">
        <ShieldCheck className="w-3 h-3 text-emerald-400" />
        <span>Grounded in Approved Records</span>
      </div>

      {/* Expanded Modal/Popover with full compliance text */}
      {expanded && (
        <div className="fixed top-12 left-1/2 -translate-x-1/2 z-50 w-full max-w-xl p-4 bg-slate-900 border border-amber-500/40 rounded-xl shadow-2xl text-xs space-y-2 text-slate-200 animate-in fade-in zoom-in-95 duration-150">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="font-bold text-amber-300 flex items-center gap-2 text-sm">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              Industrial Safety & Governance Advisory
            </span>
            <button
              onClick={() => setExpanded(false)}
              className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <p className="leading-relaxed text-slate-300">
            IntelGraphAI acts exclusively as an engineering decision-support tool. AI synthesized summaries, failure correlation hypotheses, and maintenance patterns do not replace authorized site operating procedures (SOPs), manufacturer technical manuals, or lock-out/tag-out (LOTO) safety protocols.
          </p>
          <div className="pt-2 text-[11px] font-mono text-emerald-400 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>All AI inferences require citation verification against approved plant records.</span>
          </div>
        </div>
      )}
    </div>
  );
}
