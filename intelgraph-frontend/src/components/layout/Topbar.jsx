import React, { useState } from 'react';
import { 
  Search, 
  User, 
  ChevronRight, 
  RotateCw, 
  Sparkles, 
  CheckCircle2, 
  FileCheck2,
  Check
} from 'lucide-react';
import { api } from '../../services/api';

export default function Topbar({ 
  currentRole, 
  setCurrentRole, 
  activeAsset, 
  onOpenSearch, 
  onOpenChat,
  onReseedCompleted 
}) {
  const [isReseeding, setIsReseeding] = useState(false);
  const [roleMenuOpen, setRoleMenuOpen] = useState(false);

  const roles = [
    { id: 'Maintenance Engineer', desc: 'Prioritizing maintenance due, findings, failures, and components' },
    { id: 'Quality / Compliance User', desc: 'Prioritizing evidence gaps, document governance, and audit trails' },
    { id: 'Plant Manager', desc: 'Prioritizing critical assets, open actions, and fleet availability' },
  ];

  const handleReseed = async () => {
    if (confirm('Reset operational demo dataset (P-101 bearing history, C-201 overhaul, P-102 standby, P-205)?')) {
      setIsReseeding(true);
      try {
        await api.reseed();
        if (onReseedCompleted) onReseedCompleted();
      } catch (e) {
        alert('Failed to reset: ' + e.message);
      } finally {
        setIsReseeding(false);
      }
    }
  };

  return (
    <header className="h-14 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 px-6 flex items-center justify-between gap-4 sticky top-0 z-30">
      {/* Breadcrumb Hierarchy */}
      <div className="flex items-center gap-2 text-xs text-slate-400 overflow-hidden truncate">
        <span className="text-slate-400 font-medium">Apex Energy</span>
        <ChevronRight className="w-3.5 h-3.5 text-slate-400 shrink-0" />
        <span className="text-slate-300 font-semibold">Plant A</span>
        <ChevronRight className="w-3.5 h-3.5 text-slate-400 shrink-0" />
        <span className="text-slate-400">Unit 2</span>
        <ChevronRight className="w-3.5 h-3.5 text-slate-400 shrink-0" />
        {activeAsset ? (
          <span className="text-brand-400 font-mono font-bold px-2 py-0.5 rounded bg-brand-500/10 border border-brand-500/20 truncate">
            {activeAsset.tag} — {activeAsset.name}
          </span>
        ) : (
          <span className="text-slate-300 font-medium">Operations Center</span>
        )}
      </div>

      {/* Center/Right Operator Controls */}
      <div className="flex items-center gap-3">
        {/* Operator Grounding Status Indicator (No FAISS jargon) */}
        <div className="hidden xl:flex items-center gap-3 text-[11px] font-mono pr-2 border-r border-slate-800">
          <span className="flex items-center gap-1 text-emerald-400">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Grounded in approved records</span>
          </span>
          <span className="text-slate-400">•</span>
          <span className="flex items-center gap-1 text-slate-400">
            <FileCheck2 className="w-3.5 h-3.5 text-purple-400" />
            <span>8 documents available to AI</span>
          </span>
        </div>

        {/* Global Search Button */}
        <button
          onClick={onOpenSearch}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 border border-slate-700/70 text-slate-400 hover:text-slate-200 text-xs transition-all shadow-inner"
          aria-label="Global Search"
        >
          <Search className="w-3.5 h-3.5 text-slate-400" />
          <span className="hidden sm:inline">Search machinery, records...</span>
          <kbd className="hidden md:inline-block px-1.5 py-0.5 text-[10px] font-mono bg-slate-900 rounded border border-slate-700 text-slate-400">
            ⌘K
          </kbd>
        </button>

        {/* AI Assistant Quick Trigger */}
        <button
          onClick={onOpenChat}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-600/15 hover:bg-purple-600/25 border border-purple-500/30 text-purple-300 text-xs font-medium transition-all shadow-sm"
        >
          <Sparkles className="w-3.5 h-3.5 text-purple-400" />
          <span>Ask Knowledge AI</span>
        </button>

        {/* Reseed Data Button (Subtle reset) */}
        <button
          onClick={handleReseed}
          disabled={isReseeding}
          title="Reset database to baseline demonstration state"
          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 border border-slate-700 text-xs transition-all flex items-center justify-center disabled:opacity-50"
        >
          <RotateCw className={`w-3.5 h-3.5 ${isReseeding ? 'animate-spin text-brand-400' : ''}`} />
        </button>

        {/* Role Switcher */}
        <div className="relative">
          <button
            onClick={() => setRoleMenuOpen(!roleMenuOpen)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700/80 border border-slate-700 text-slate-200 text-xs font-medium transition-all"
          >
            <User className="w-3.5 h-3.5 text-brand-400" />
            <span className="hidden lg:inline">{currentRole}</span>
          </button>

          {roleMenuOpen && (
            <div className="absolute right-0 mt-2 w-72 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-2 z-50 animate-in fade-in zoom-in-95 duration-150">
              <div className="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800 mb-1">
                Operational Perspective
              </div>
              {roles.map((r) => (
                <button
                  key={r.id}
                  onClick={() => {
                    setCurrentRole(r.id);
                    setRoleMenuOpen(false);
                  }}
                  className={`w-full text-left p-2.5 rounded-lg text-xs transition-all ${
                    currentRole === r.id
                      ? 'bg-brand-500/15 text-brand-400 border border-brand-500/30'
                      : 'hover:bg-slate-800 text-slate-300'
                  }`}
                >
                  <div className="font-semibold flex items-center justify-between">
                    <span>{r.id}</span>
                    {currentRole === r.id && <Check className="w-3.5 h-3.5 text-brand-400" />}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">{r.desc}</div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
