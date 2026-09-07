import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  GitBranch, 
  Play, 
  AlertTriangle, 
  CheckCircle2, 
  ExternalLink, 
  RotateCw,
  Sparkles,
  Layers,
  Wrench
} from 'lucide-react';
import { api } from '../../services/api';
import InformationBadge from '../common/InformationBadge';

export default function ReportsView({ onSelectAsset, onOpenDocViewer }) {
  const [assetTag, setAssetTag] = useState('P-101');
  const [problemText, setProblemText] = useState('High Vibration & Bearing Seizure');
  const [rcaResult, setRcaResult] = useState(null);
  const [loadingRCA, setLoadingRCA] = useState(false);
  const [crossPatterns, setCrossPatterns] = useState([]);

  useEffect(() => {
    loadRCA();
    loadCrossPatterns();
  }, []);

  const loadCrossPatterns = async () => {
    try {
      const data = await api.getCrossAssetPatterns();
      setCrossPatterns(data);
    } catch (err) {
      console.error('Failed to load cross asset patterns:', err);
    }
  };

  const loadRCA = async () => {
    setLoadingRCA(true);
    try {
      const res = await api.runRCA(assetTag, problemText);
      setRcaResult(res);
    } catch (err) {
      alert('Failed to generate RCA: ' + err.message);
    } finally {
      setLoadingRCA(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <GitBranch className="w-5 h-5 text-brand-400" />
          <span>Root Cause Analysis (RCA) & Fleet Reliability Reports</span>
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Grounded cross-document failure pattern analysis linking historical work orders, condition monitoring, and OEM procedures
        </p>
      </div>

      {/* SECTION 1: ROOT CAUSE ANALYSIS STUDIO */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-6 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-brand-500/10 text-brand-400 border border-brand-500/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <span>AI-Assisted Root Cause Analysis</span>
                <InformationBadge type="ai" label="Decision Support" />
              </h3>
              <p className="text-xs text-slate-400">
                Correlates maintenance work orders, inspection logs, and OEM manual thresholds
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={assetTag}
              onChange={(e) => setAssetTag(e.target.value)}
              className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-xs text-brand-400 font-bold font-mono focus:border-brand-500"
            >
              <option value="P-101">P-101 (Centrifugal Pump)</option>
              <option value="P-102">P-102 (Booster Pump)</option>
              <option value="C-201">C-201 (Compressor)</option>
            </select>

            <button
              onClick={loadRCA}
              disabled={loadingRCA}
              className="px-4 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white font-bold text-xs flex items-center gap-1.5 transition-all shadow-md shadow-brand-500/20 disabled:opacity-50"
            >
              {loadingRCA ? <RotateCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
              <span>Run Analysis</span>
            </button>
          </div>
        </div>

        {/* RCA Content Breakdown */}
        {loadingRCA ? (
          <div className="py-12 text-center text-slate-400">
            <div className="w-8 h-8 border-2 border-brand-400 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
            Correlating historical records and OEM tolerance procedures...
          </div>
        ) : rcaResult ? (
          <div className="space-y-6 text-xs animate-in fade-in duration-200">
            {/* 1. Observed Problem */}
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
              <span className="text-[10px] uppercase font-mono text-slate-400 font-semibold">Observed Problem</span>
              <h4 className="text-base font-bold text-red-400">{rcaResult.observed_problem}</h4>
              <p className="text-slate-400 text-xs">Evaluated against asset {rcaResult.asset_tag} historical database.</p>
            </div>

            {/* 2. Historical Evidence Chain */}
            <div className="p-5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
              <h4 className="font-bold text-white text-xs uppercase tracking-wider flex items-center gap-2">
                <FileText className="w-4 h-4 text-brand-400" />
                <span>Historical Evidence Timeline</span>
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {rcaResult.historical_evidence?.map((ev, i) => (
                  <div key={i} className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                    <div className="flex items-center justify-between font-mono text-[10px] text-brand-400">
                      <span>{ev.record_id}</span>
                      <span>{ev.date}</span>
                    </div>
                    <p className="text-slate-300 font-mono text-[11px] leading-relaxed">{ev.summary}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* 3. Possible Causes (Supported by Data Only) */}
            <div className="p-5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
              <h4 className="font-bold text-white text-xs uppercase tracking-wider flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <span>Supported Probable Root Causes</span>
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {rcaResult.possible_causes?.map((c, i) => (
                  <div key={i} className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white text-xs">{c.cause}</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-brand-500/10 text-brand-400 font-mono">
                        {c.confidence} Confidence
                      </span>
                    </div>
                    <p className="text-slate-300 text-[11px] leading-relaxed">{c.evidence}</p>
                    <div className="text-[10px] font-mono text-purple-400 pt-1 border-t border-slate-800">
                      Source: {c.source_doc}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 4. Recommended OEM Checks */}
            <div className="p-5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
              <h4 className="font-bold text-white text-xs uppercase tracking-wider flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Recommended OEM Verification Checks</span>
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {rcaResult.recommended_checks?.map((chk, i) => (
                  <div key={i} className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                    <div className="font-semibold text-emerald-300 text-xs">
                      {i + 1}. {chk.step}
                    </div>
                    <div className="text-[11px] font-mono text-slate-200">
                      Target Spec: <strong>{chk.target_spec}</strong>
                    </div>
                    <div className="text-[10px] font-mono text-slate-400">
                      Procedure: {chk.source_procedure}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Disclaimer */}
            <div className="p-3 rounded-lg bg-amber-950/20 border border-amber-500/20 text-amber-300 text-[11px]">
              <strong>Notice:</strong> {rcaResult.disclaimer}
            </div>
          </div>
        ) : null}
      </div>

      {/* SECTION 2: FLEET-WIDE CROSS-ASSET ANOMALY PATTERNS */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 shadow-xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <Layers className="w-5 h-5 text-cyan-400" />
            <div>
              <h3 className="text-sm font-bold text-white">
                Fleet-Wide Failure Intelligence & Correlation
              </h3>
              <p className="text-xs text-slate-400">
                Identifies recurring failure modes and vibration anomalies across multiple plant assets
              </p>
            </div>
          </div>
          <span className="text-xs font-mono text-brand-400">Cross-Asset Discovery</span>
        </div>

        <div className="space-y-3">
          {crossPatterns.map((pat, idx) => (
            <div key={idx} className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-2">
              <div className="flex items-center justify-between font-semibold">
                <span className="text-sm text-cyan-300">{pat.pattern_title}</span>
                <span className="font-mono text-slate-400">
                  Affected Machinery: <strong>{pat.affected_assets.join(', ')}</strong>
                </span>
              </div>
              <p className="text-slate-300 leading-relaxed">{pat.summary}</p>
              <div className="p-2.5 rounded bg-slate-900 text-brand-300 text-[11px] font-mono">
                <strong>Recommended Fleet Action:</strong> {pat.recommended_action}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
