import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  AlertTriangle, 
  CheckCircle2, 
  FileText, 
  ArrowRight,
  ExternalLink,
  FileCheck2,
  Download,
  RotateCw,
  X,
  Lock,
  Award
} from 'lucide-react';
import { api } from '../../services/api';
import EvidenceDrawer from '../common/EvidenceDrawer';

export default function ComplianceView({ onSelectAsset, currentRole = 'Quality / Compliance Auditor', currentPersona }) {
  const [complianceSummary, setComplianceSummary] = useState(null);
  const [selectedAsset, setSelectedAsset] = useState('P-101');
  const [assetAuditItems, setAssetAuditItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [evidenceDrawerOpen, setEvidenceDrawerOpen] = useState(false);
  const [selectedEvidence, setSelectedEvidence] = useState(null);

  // Evidence Package Modal State
  const [generatingPackage, setGeneratingPackage] = useState(false);
  const [packageData, setPackageData] = useState(null);

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

  const handleGeneratePackage = async () => {
    setGeneratingPackage(true);
    try {
      const auditorName = currentPersona?.full_name || currentPersona?.name || 'Lead Compliance Auditor';
      const pkg = await api.generateCompliancePackage(selectedAsset, 'API 610 / ISO 10816-3', auditorName);
      setPackageData(pkg);
    } catch (err) {
      alert('Failed to generate audit evidence package: ' + err.message);
    } finally {
      setGeneratingPackage(false);
    }
  };

  const handleDownloadJSON = () => {
    if (!packageData) return;
    const blob = new Blob([JSON.stringify(packageData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${packageData.package_id}_Audit_Package.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const satisfiedCount = assetAuditItems.filter(i => i.status === 'Compliant' || i.status.includes('Satisfied')).length;
  const underReviewCount = assetAuditItems.filter(i => i.status.includes('Under Review') || i.status.includes('Pending')).length;
  const gapCount = assetAuditItems.length - satisfiedCount - underReviewCount;

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="text-xs font-mono tracking-wider uppercase text-slate-400 font-semibold mb-1">
            Evidence-First Verification & Audit Intelligence
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-emerald-400" />
            <span>Compliance & Regulatory Audit Dossier</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Trace mandatory mechanical, safety, and statutory standards (OISD, PESO, Factories Act, API, OSHA, ISO) back to verified engineering records
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
            <option value="P-203">P-203 (Secondary Injection Pump)</option>
            <option value="P-307">P-307 (Produced Water Pump)</option>
            <option value="P-205">P-205 (Slurry Pump)</option>
          </select>
        </div>
      </div>

      {/* 1. EVIDENCE-FIRST COMPLIANCE STATUS BANNER & PACKAGE GENERATOR */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block">
            Compliance Status ({selectedAsset})
          </span>
          <div className="text-lg font-bold text-white mt-1 flex flex-wrap items-center gap-2">
            <span className="text-emerald-400 font-mono text-sm px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
              {satisfiedCount} Satisfied
            </span>
            <span className="text-blue-400 font-mono text-sm px-2 py-0.5 rounded bg-blue-500/10 border border-blue-500/20">
              {underReviewCount} Under Review
            </span>
            <span className="text-amber-400 font-mono text-sm px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/20">
              {gapCount} Gap{gapCount !== 1 ? 's' : ''} Identified
            </span>
            <span className="text-slate-400 font-normal text-xs ml-1">• {assetAuditItems.length} standards evaluated</span>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={handleGeneratePackage}
            disabled={generatingPackage}
            className="px-4 py-2 rounded-xl bg-brand-500/15 hover:bg-brand-500/25 text-brand-300 font-bold text-xs border border-brand-500/30 transition-all flex items-center gap-2 shadow-sm disabled:opacity-50"
          >
            {generatingPackage ? <RotateCw className="w-4 h-4 animate-spin text-brand-400" /> : <FileCheck2 className="w-4 h-4 text-brand-400" />}
            <span>{generatingPackage ? 'Generating Package...' : 'Generate Audit Evidence Package'}</span>
          </button>

          <button
            onClick={() => onSelectAsset(selectedAsset)}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-750 text-brand-400 font-semibold text-xs border border-slate-700 transition-all flex items-center gap-1.5 shadow-sm"
          >
            <span>Open Machine ({selectedAsset})</span>
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
              const isSatisfied = item.status === 'Compliant' || item.status.includes('Satisfied');
              const isUnderReview = item.status.includes('Under Review') || item.status.includes('Pending');
              const isGap = !isSatisfied && !isUnderReview;

              return (
                <div
                  key={item.audit_id}
                  className={`p-5 rounded-2xl border transition-all ${
                    isSatisfied
                      ? 'bg-slate-900 border-slate-800'
                      : isUnderReview
                        ? 'bg-blue-950/15 border-blue-500/30'
                        : 'bg-amber-950/15 border-amber-500/30'
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                          isSatisfied
                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                            : isUnderReview
                              ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                              : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                        }`}>
                          {item.status}
                        </span>
                        <span className="text-xs font-mono font-semibold text-slate-400">
                          {item.regulatory_body}
                        </span>
                        <span className="text-slate-600">•</span>
                        <h3 className="font-bold text-sm text-white">{item.requirement_title}</h3>
                      </div>
                      <p className="text-xs text-slate-400">{item.description}</p>
                    </div>

                    <div className="shrink-0">
                      <button
                        onClick={() => handleReviewEvidence(item)}
                        className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-all flex items-center gap-1.5"
                      >
                        <FileText className="w-3.5 h-3.5 text-brand-400" />
                        <span>Inspect Evidence</span>
                      </button>
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-800/80 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div>
                      <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block mb-1">
                        Mandated Requirement
                      </span>
                      <p className="text-slate-300 font-mono text-[11px] leading-relaxed">
                        {item.required_evidence}
                      </p>
                    </div>
                    <div>
                      <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block mb-1">
                        Verified Evidence on File
                      </span>
                      <p className={`font-mono text-[11px] leading-relaxed ${
                        isSatisfied 
                          ? 'text-emerald-400' 
                          : isUnderReview 
                            ? 'text-blue-300 font-medium' 
                            : 'text-amber-400 font-semibold'
                      }`}>
                        {item.available_evidence || 'NO RECORD FOUND — Compliance Gap Documented'}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* REGULATORY AUDIT EVIDENCE PACKAGE MODAL */}
      {packageData && (
        <div className="fixed inset-0 z-50 bg-slate-950/85 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400">
                  <Award className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-base flex items-center gap-2">
                    <span>Regulatory Audit Evidence Package</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-brand-500/15 text-brand-400 border border-brand-500/30 font-bold">
                      {packageData.package_id}
                    </span>
                  </h3>
                  <p className="text-xs text-slate-400 font-mono">
                    Target Machine: <strong className="text-brand-400">{packageData.asset_tag}</strong> • Standards: {packageData.regulatory_standards_covered?.join(', ')}
                  </p>
                </div>
              </div>

              <button
                onClick={() => setPackageData(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Scrollable Body */}
            <div className="p-6 overflow-y-auto space-y-5 text-xs">
              {/* Provenance & Cryptographic Signature Box */}
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 font-mono text-[11px]">
                  <div className="text-slate-400">
                    Generated By: <strong className="text-slate-200">{packageData.generated_by}</strong>
                  </div>
                  <div className="text-slate-400">
                    Timestamp: <strong className="text-slate-200">{packageData.generated_at}</strong>
                  </div>
                </div>
                <div className="pt-2 border-t border-slate-800 text-[11px] font-mono flex items-center gap-2">
                  <Lock className="w-3.5 h-3.5 text-brand-400 shrink-0" />
                  <span className="text-slate-400">SHA-256 Digital Fingerprint:</span>
                  <span className="text-brand-400 truncate font-semibold">
                    {packageData.cryptographic_fingerprint_sha256}
                  </span>
                </div>
              </div>

              {/* Regulatory Audit Declaration */}
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-300 text-xs leading-relaxed">
                <strong className="text-white">Auditor Declaration:</strong> {packageData.declaration}
              </div>

              {/* Requirement-to-Evidence Matrix */}
              <div className="space-y-3">
                <h4 className="font-bold text-white text-xs uppercase tracking-wider">
                  Itemized Requirement & Evidence Matrix ({packageData.evidence_matrix?.length || 0} Standard Items)
                </h4>
                <div className="space-y-2.5">
                  {packageData.evidence_matrix?.map((m, idx) => {
                    const isPassed = m.status === 'Compliant';
                    return (
                      <div
                        key={idx}
                        className={`p-3.5 rounded-xl border ${
                          isPassed ? 'bg-slate-950/70 border-slate-800' : 'bg-amber-950/20 border-amber-500/30'
                        }`}
                      >
                        <div className="flex items-center justify-between font-semibold mb-1">
                          <span className="text-white text-xs flex items-center gap-2">
                            <span className="font-mono text-brand-400">{m.standard}</span>
                            <span>{m.requirement}</span>
                          </span>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                            isPassed ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
                          }`}>
                            {m.status}
                          </span>
                        </div>
                        <div className="text-[11px] font-mono text-slate-300">
                          Required: <span className="text-slate-400">{m.mandated_evidence}</span>
                        </div>
                        <div className="text-[11px] font-mono text-slate-300 pt-0.5">
                          Verified File: <strong className={isPassed ? 'text-emerald-400' : 'text-amber-400'}>{m.verified_file}</strong>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-800 flex items-center justify-between bg-slate-950/60">
              <span className="text-xs text-slate-400 font-mono">
                Official Regulatory Package • Ready for ISO 27001 / API 610 Submissions
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleDownloadJSON}
                  className="px-4 py-2 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-bold text-xs flex items-center gap-2 transition-all shadow-md shadow-brand-500/20"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download Audit Package (.json)</span>
                </button>
                <button
                  onClick={() => setPackageData(null)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs transition-all"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
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
