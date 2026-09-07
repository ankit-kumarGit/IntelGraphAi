import React, { useState } from 'react';
import { AlertCircle, FileText, CheckCircle2, ArrowRight } from 'lucide-react';
import EvidenceDrawer from '../common/EvidenceDrawer';

export default function TabFindings({ assetTag, findings = [], onOpenDocViewer }) {
  const [evidenceDrawerOpen, setEvidenceDrawerOpen] = useState(false);
  const [selectedEvidence, setSelectedEvidence] = useState(null);

  const handleOpenEvidence = (finding) => {
    setSelectedEvidence([
      {
        document_name: finding.evidence_summary || 'Historical Verification Records',
        date: '2026-02-22',
        page: '1',
        status: 'Verified',
        excerpt: `Observed: ${finding.title}. ${finding.evidence_summary}`
      }
    ]);
    setEvidenceDrawerOpen(true);
  };

  if (!findings || findings.length === 0) {
    return (
      <div className="p-12 text-center text-slate-400 bg-slate-900/50 rounded-xl border border-slate-800">
        <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2 opacity-50" />
        <h4 className="text-sm font-semibold text-slate-300">No Open Operational Findings</h4>
        <p className="text-xs text-slate-400 mt-1">
          All historical maintenance and condition monitoring records for {assetTag} are in nominal standing.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between p-4 rounded-xl bg-slate-900 border border-slate-800 text-xs">
        <div>
          <h3 className="font-bold text-white text-sm">Action-Oriented Findings</h3>
          <p className="text-slate-400 text-[11px]">
            Strictly supported by historical work orders and condition monitoring inspection logs
          </p>
        </div>
        <span className="px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-300 text-xs font-semibold border border-amber-500/20">
          {findings.length} Open Item{findings.length > 1 ? 's' : ''}
        </span>
      </div>

      <div className="space-y-4">
        {findings.map((f) => (
          <div
            key={f.finding_id}
            className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 shadow-lg"
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2.5">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-400"></span>
                <h4 className="font-bold text-sm text-white">{f.title}</h4>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded font-mono text-[10px] font-semibold uppercase bg-amber-500/15 text-amber-300 border border-amber-500/30">
                  Status: {f.status}
                </span>
              </div>
            </div>

            {/* Structure: WHAT OBSERVED / WHY IT MATTERS / EVIDENCE / WHAT SHOULD BE REVIEWED */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1">
                <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block">
                  What Was Observed?
                </span>
                <p className="text-slate-200 leading-relaxed font-medium">
                  {f.title}
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1">
                <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block">
                  Why Does It Matter?
                </span>
                <p className="text-slate-300 leading-relaxed">
                  Historical records show repeated bearing-related events across multiple operating intervals.
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1">
                <span className="text-[10px] font-mono uppercase tracking-wider text-brand-400 font-semibold block">
                  Supporting Evidence Records
                </span>
                <p className="text-slate-300 font-mono text-[11px]">
                  {f.evidence_summary}
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-purple-950/20 border border-purple-500/30 space-y-1">
                <span className="text-[10px] font-mono uppercase tracking-wider text-purple-300 font-semibold block">
                  What Should Be Reviewed?
                </span>
                <p className="text-purple-200 leading-relaxed font-medium">
                  {f.recommended_action}
                </p>
                <div className="text-[10px] text-purple-400/80 font-mono pt-1">
                  Governing Procedure: {f.source_procedure}
                </div>
              </div>
            </div>

            {/* Footer Owner & Actions */}
            <div className="flex items-center justify-between pt-1 border-t border-slate-800 text-xs">
              <span className="text-slate-400">
                Assigned Owner: <strong className="text-slate-200">{f.owner}</strong>
              </span>

              <button
                onClick={() => handleOpenEvidence(f)}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-brand-400 hover:text-brand-300 font-semibold text-xs border border-slate-700 transition-all flex items-center gap-1.5"
              >
                <FileText className="w-3.5 h-3.5" />
                <span>View Evidence</span>
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Evidence Drawer */}
      <EvidenceDrawer
        isOpen={evidenceDrawerOpen}
        onClose={() => setEvidenceDrawerOpen(false)}
        evidenceData={selectedEvidence}
        onOpenDocViewer={onOpenDocViewer}
      />
    </div>
  );
}
