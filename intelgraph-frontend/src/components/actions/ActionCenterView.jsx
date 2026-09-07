import React, { useState, useEffect } from 'react';
import { 
  AlertCircle, 
  Wrench, 
  ShieldAlert, 
  CheckCircle2, 
  ArrowRight, 
  ChevronDown, 
  ChevronUp, 
  FileText,
  Clock,
  User
} from 'lucide-react';
import { api } from '../../services/api';
import EvidenceDrawer from '../common/EvidenceDrawer';

export default function ActionCenterView({ onSelectAsset }) {
  const [actions, setActions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('all');
  const [expandedId, setExpandedId] = useState(null);
  const [evidenceDrawerOpen, setEvidenceDrawerOpen] = useState(false);
  const [selectedEvidence, setSelectedEvidence] = useState(null);

  useEffect(() => {
    let isMounted = true;
    async function loadActions() {
      setLoading(true);
      try {
        const data = await api.getActions();
        if (isMounted) setActions(data);
      } catch (err) {
        console.error('Failed to load action items:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadActions();
    return () => { isMounted = false; };
  }, []);

  const filtered = filterType === 'all' 
    ? actions 
    : actions.filter(a => a.type === filterType);

  const handleOpenEvidence = (act) => {
    setSelectedEvidence([
      {
        document_name: act.evidence || 'Industrial Action Record',
        date: '2026-02-22',
        page: '1',
        status: 'Verified',
        excerpt: `${act.title}: ${act.why_it_matters}`
      }
    ]);
    setEvidenceDrawerOpen(true);
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="text-xs font-mono tracking-wider uppercase text-slate-400 font-semibold mb-1">
            Operational Queue
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <span>Action Center</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Prioritized operational queue of maintenance overhauls, findings, and compliance reviews
          </p>
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto text-xs">
          {['all', 'Maintenance Due', 'Open Finding', 'Compliance Gap'].map((t) => (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              className={`px-3 py-1.5 rounded-lg capitalize font-medium whitespace-nowrap transition-all ${
                filterType === t
                  ? 'bg-brand-500/15 text-brand-400 border border-brand-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Operational Queue */}
      {loading ? (
        <div className="p-16 text-center text-slate-400">
          <div className="w-8 h-8 border-2 border-brand-400 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          Evaluating operational queue...
        </div>
      ) : filtered.length === 0 ? (
        <div className="p-12 text-center text-slate-400 bg-slate-900/50 rounded-xl border border-slate-800">
          <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2 opacity-50" />
          <h4 className="text-sm font-semibold text-slate-300">All Operations Clear</h4>
          <p className="text-xs text-slate-400 mt-1">No pending maintenance overhauls, open findings, or compliance gaps found.</p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {filtered.map((act) => {
            const isExpanded = expandedId === act.action_id;
            const isCrit = act.severity === 'Critical';

            return (
              <div
                key={act.action_id}
                className={`rounded-xl border transition-all ${
                  isCrit
                    ? 'bg-red-950/15 border-red-500/30'
                    : 'bg-slate-900 border-slate-800 hover:border-slate-700'
                }`}
              >
                {/* Collapsed State (Progressive Disclosure) */}
                <div className="p-4 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 min-w-0">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                      isCrit ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400'
                    }`}>
                      {act.severity}
                    </span>

                    <button
                      onClick={() => onSelectAsset(act.asset_tag)}
                      className="font-mono font-bold text-xs text-white hover:text-brand-400 transition-colors"
                    >
                      {act.asset_tag}
                    </button>

                    <span className="text-slate-400 text-xs hidden sm:inline">•</span>

                    <span className="font-semibold text-xs text-slate-200 truncate">
                      {act.title}
                    </span>

                    <span className="text-slate-400 text-xs hidden md:inline truncate">
                      — {act.why_it_matters}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => setExpandedId(isExpanded ? null : act.action_id)}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-all flex items-center gap-1"
                    >
                      <span>{isExpanded ? 'Collapse' : 'Review'}</span>
                      {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>

                {/* Expanded State */}
                {isExpanded && (
                  <div className="px-5 pb-5 pt-2 border-t border-slate-800/80 space-y-4 text-xs animate-in fade-in duration-150">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800">
                        <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block mb-1">
                          Why This Matters
                        </span>
                        <p className="text-slate-300 leading-relaxed">{act.why_it_matters}</p>
                      </div>

                      <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800">
                        <span className="text-[10px] font-mono uppercase tracking-wider text-brand-400 font-semibold block mb-1">
                          What Needs Action?
                        </span>
                        <p className="text-slate-200 font-medium leading-relaxed">{act.what_needs_action}</p>
                      </div>

                      <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800 flex flex-col justify-between">
                        <div>
                          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block mb-1">
                            Evidence
                          </span>
                          <p className="text-slate-300 font-mono text-[11px]">{act.evidence}</p>
                        </div>
                        <div className="pt-2 flex items-center justify-between text-[11px] text-slate-400">
                          <span>Owner: <strong className="text-slate-200">{act.owner}</strong></span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-1">
                      <button
                        onClick={() => handleOpenEvidence(act)}
                        className="text-xs text-brand-400 hover:text-brand-300 font-medium flex items-center gap-1.5 transition-colors"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        <span>View Evidence</span>
                      </button>

                      <button
                        onClick={() => onSelectAsset(act.asset_tag)}
                        className="px-3.5 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white font-semibold text-xs flex items-center gap-1.5 transition-all shadow-md shadow-brand-500/20"
                      >
                        <span>Open Machine Brain ({act.asset_tag})</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Evidence Drawer */}
      <EvidenceDrawer
        isOpen={evidenceDrawerOpen}
        onClose={() => setEvidenceDrawerOpen(false)}
        evidenceData={selectedEvidence}
      />
    </div>
  );
}
