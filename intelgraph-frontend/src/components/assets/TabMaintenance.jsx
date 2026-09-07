import React, { useState } from 'react';
import { 
  Wrench, 
  Calendar, 
  AlertTriangle, 
  ChevronDown, 
  ChevronUp, 
  FileText, 
  User, 
  Clock 
} from 'lucide-react';
import EvidenceDrawer from '../common/EvidenceDrawer';

export default function TabMaintenance({ assetTag, maintenanceData }) {
  const [expandedWoId, setExpandedWoId] = useState(null);
  const [evidenceDrawerOpen, setEvidenceDrawerOpen] = useState(false);
  const [selectedEvidence, setSelectedEvidence] = useState(null);

  const workOrders = maintenanceData?.work_orders || [];
  const recurring = maintenanceData?.recurring_patterns || [];

  const handleOpenEvidence = (wo) => {
    setSelectedEvidence([
      {
        document_name: `Work Order ${wo.work_order_number}`,
        date: wo.date,
        page: '1',
        technician: wo.technician,
        status: 'Verified Record',
        excerpt: `${wo.description} Replaced: ${wo.components_replaced?.join(', ') || 'None'}. Observations: ${wo.findings || 'Nominal'}`
      }
    ]);
    setEvidenceDrawerOpen(true);
  };

  return (
    <div className="space-y-6">
      {/* 1. NEXT MAINTENANCE CARD */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block">
            Next Scheduled Maintenance
          </span>
          <div className="text-base font-bold text-white mt-0.5 flex items-center gap-2">
            <Calendar className="w-4 h-4 text-brand-400" />
            <span>12 Sep 2026 (Semi-Annual Bearing & Alignment Service)</span>
          </div>
        </div>
        <span className="text-xs font-mono px-3 py-1 rounded-full bg-slate-800 text-brand-400 border border-slate-700">
          In 7 Days
        </span>
      </div>

      {/* 2. RECURRING PATTERNS ALERT */}
      {recurring.length > 0 && (
        <div className="p-4 rounded-xl bg-amber-950/25 border border-amber-500/30 space-y-2 text-xs">
          <div className="flex items-center gap-2 font-bold text-amber-300">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <span>Detected Recurring Maintenance Pattern</span>
          </div>
          {recurring.map((p, idx) => (
            <div key={idx} className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 space-y-1">
              <span className="font-semibold text-white">{p.pattern}</span>
              <p className="text-slate-300 leading-relaxed">{p.observation}</p>
            </div>
          ))}
        </div>
      )}

      {/* 3. RECENT HISTORY (Collapsed Work Orders) */}
      <div className="space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
          Maintenance History & Interventions ({workOrders.length})
        </h3>

        <div className="space-y-2">
          {workOrders.map((wo) => {
            const isExpanded = expandedWoId === wo.record_id;
            return (
              <div
                key={wo.record_id}
                className="rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all"
              >
                {/* Collapsed Header */}
                <div className="p-4 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 min-w-0">
                    <span className="font-mono font-bold text-xs text-brand-400">
                      {wo.work_order_number}
                    </span>
                    <span className="text-slate-400 text-xs">•</span>
                    <span className="font-semibold text-xs text-white truncate">
                      {wo.record_type}
                    </span>
                    <span className="text-slate-400 text-xs hidden sm:inline">
                      ({wo.date.substring(0, 4)})
                    </span>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <span className="text-slate-400 text-[11px] font-mono hidden md:inline">
                      Tech: {wo.technician}
                    </span>
                    <button
                      onClick={() => setExpandedWoId(isExpanded ? null : wo.record_id)}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-all flex items-center gap-1"
                    >
                      <span>{isExpanded ? 'Hide' : 'Details'}</span>
                      {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="px-5 pb-5 pt-1 border-t border-slate-800/80 space-y-3 text-xs animate-in fade-in duration-150">
                    <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800 space-y-1 mt-2">
                      <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block">
                        Intervention Summary
                      </span>
                      <p className="text-slate-200 leading-relaxed font-sans">{wo.description}</p>
                    </div>

                    {wo.components_replaced?.length > 0 && (
                      <div className="flex items-center gap-2 pt-1">
                        <span className="text-slate-400">Replaced Components:</span>
                        <div className="flex flex-wrap gap-1.5">
                          {wo.components_replaced.map((c, i) => (
                            <span key={i} className="px-2 py-0.5 rounded bg-slate-800 text-cyan-300 font-mono text-[11px]">
                              {c}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {wo.findings && (
                      <div className="p-2.5 rounded bg-amber-950/20 border border-amber-500/20 text-slate-300 text-[11px]">
                        <strong className="text-amber-300">Technician Observations:</strong> {wo.findings}
                      </div>
                    )}

                    <div className="flex justify-end pt-1">
                      <button
                        onClick={() => handleOpenEvidence(wo)}
                        className="text-xs text-brand-400 hover:text-brand-300 font-medium flex items-center gap-1.5"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        <span>View Work Order Evidence</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Evidence Drawer */}
      <EvidenceDrawer
        isOpen={evidenceDrawerOpen}
        onClose={() => setEvidenceDrawerOpen(false)}
        evidenceData={selectedEvidence}
      />
    </div>
  );
}
