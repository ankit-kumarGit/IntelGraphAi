import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  AlertTriangle, 
  CheckCircle2, 
  FileText, 
  ArrowRight,
  ExternalLink 
} from 'lucide-react';
import { api } from '../../services/api';
import EvidenceDrawer from '../common/EvidenceDrawer';

export default function ComplianceView({ onSelectAsset }) {
  const [complianceSummary, setComplianceSummary] = useState(null);
  const [selectedAsset, setSelectedAsset] = useState('P-101');
  const [assetAuditItems, setAssetAuditItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [evidenceDrawerOpen, setEvidenceDrawerOpen] = useState(false);
  const [selectedEvidence, setSelectedEvidence] = useState(null);

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      setLoading(true);
      try {
        const overview = await api.getOverview('Quality / Compliance User');
        const items = await api.getCompliance(selectedAsset);
        if (isMounted) {
          setComplianceSummary(overview.compliance_summary);
          setAssetAuditItems(items);
        }
      } catch (err) {
        console.error('Failed to load compliance:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadData();
    return () => { isMounted = false; };
  }, [selectedAsset]);

  const handleReviewEvidence = (item) => {
    setSelectedEvidence([
      {
        document_name: item.available_evidence || item.requirement_title,
        date: 'Verified Record',
        page: '1',
        status: item.status === 'Compliant' ? 'Verified' : 'Evidence Gap',
        excerpt: item.available_evidence 
          ? `Verified documentation on file for ${item.regulatory_body} standard: ${item.available_evidence}`
          : `Audit Evidence Gap: ${item.required_evidence} is missing from the asset knowledge profile.`
      }
    ]);
    setEvidenceDrawerOpen(true);
  };

  const gapCount = assetAuditItems.filter(i => i.status !== 'Compliant').length;

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="text-xs font-mono tracking-wider uppercase text-slate-400 font-semibold mb-1">
            Evidence-First Verification
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-emerald-400" />
            <span>Compliance & Evidence Gaps</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Trace mandatory mechanical and instrumentation standards back to verified engineering records
          </p>
        </div>

        {/* Target Asset Selector */}
        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-400 font-medium">Target Machine:</span>
          <select
            value={selectedAsset}
            onChange={(e) => setSelectedAsset(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-brand-400 font-bold font-mono focus:border-brand-500"
          >
            <option value="P-101">P-101 (Centrifugal Pump)</option>
            <option value="P-102">P-102 (Booster Pump)</option>
            <option value="C-201">C-201 (Compressor)</option>
            <option value="P-205">P-205 (Slurry Pump)</option>
          </select>
        </div>
      </div>

      {/* 1. EVIDENCE-FIRST COMPLIANCE STATUS BANNER (Section 30) */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block">
            Compliance Status
          </span>
          <div className="text-xl font-bold text-white mt-0.5 flex items-center gap-2">
            <span className={gapCount > 0 ? 'text-amber-400' : 'text-emerald-400'}>
              {gapCount} evidence gap{gapCount !== 1 ? 's' : ''} detected
            </span>
            <span className="text-slate-400 font-normal text-xs">• {assetAuditItems.length} standards evaluated</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onSelectAsset(selectedAsset)}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-750 text-brand-400 font-semibold text-xs border border-slate-700 transition-all flex items-center gap-1.5 shadow-sm"
          >
            <span>Open {selectedAsset} Brain</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* 2. EVIDENCE-FIRST REQUIREMENT QUEUE */}
      <div className="space-y-3">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Standard Requirements & Verification Status
        </h2>

        {loading ? (
          <div className="p-16 text-center text-slate-400">
            <div className="w-8 h-8 border-2 border-brand-400 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
            Auditing records against regulatory standards...
          </div>
        ) : (
          <div className="space-y-3">
            {assetAuditItems.map((item) => {
              const isCompliant = item.status === 'Compliant';

              return (
                <div
                  key={item.audit_id}
                  className={`p-5 rounded-2xl border transition-all ${
                    isCompliant
                      ? 'bg-slate-900 border-slate-800'
                      : 'bg-amber-950/15 border-amber-500/30'
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
                    <div className="flex items-center gap-2.5">
                      <span className="font-mono text-xs font-bold text-brand-400 bg-brand-500/10 px-2 py-0.5 rounded border border-brand-500/20">
                        {item.regulatory_body}
                      </span>
                      <h3 className="font-bold text-sm text-white">
                        {item.requirement_title}
                      </h3>
                    </div>

                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold uppercase self-start sm:self-center border ${
                      isCompliant
                        ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                        : 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                    }`}>
                      {isCompliant ? 'Verified Compliant' : 'Evidence Gap'}
                    </span>
                  </div>

                  {/* Requirement -> Evidence -> Status -> Action Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-3 text-xs">
                    <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800">
                      <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block mb-0.5">
                        Required Evidence
                      </span>
                      <p className="text-slate-300 font-mono text-[11px]">{item.required_evidence}</p>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800">
                      <span className="text-[10px] font-mono uppercase tracking-wider text-brand-400 font-semibold block mb-0.5">
                        Available Evidence in System
                      </span>
                      {item.available_evidence ? (
                        <p className="text-slate-200 font-mono text-[11px] flex items-center gap-1">
                          <FileText className="w-3.5 h-3.5 text-brand-400 shrink-0" />
                          <span>{item.available_evidence}</span>
                        </p>
                      ) : (
                        <p className="text-amber-400 font-semibold text-[11px] flex items-center gap-1">
                          <AlertTriangle className="w-3 h-3 shrink-0" />
                          <span>Missing record</span>
                        </p>
                      )}
                    </div>

                    <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800 flex flex-col justify-between">
                      <div>
                        <span className="text-[10px] font-mono uppercase tracking-wider text-purple-300 font-semibold block mb-0.5">
                          Action Required
                        </span>
                        <p className="text-slate-300 text-[11px]">
                          {isCompliant ? 'Record archived; ready for annual external audit.' : 'Upload calibration certificate or schedule recalibration.'}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Review Evidence Button */}
                  <div className="flex justify-end pt-3 border-t border-slate-800/60 mt-3">
                    <button
                      onClick={() => handleReviewEvidence(item)}
                      className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-brand-400 hover:text-brand-300 font-semibold text-xs border border-slate-700 transition-all flex items-center gap-1.5"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      <span>Review Evidence</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
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
