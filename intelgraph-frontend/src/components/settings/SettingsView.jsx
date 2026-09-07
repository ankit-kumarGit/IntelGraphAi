import React, { useState } from 'react';
import { 
  Sliders, 
  ShieldCheck, 
  Check, 
  X, 
  Layers, 
  User, 
  Info,
  Sparkles,
  Play,
  RotateCw,
  Award,
  Zap,
  ShieldAlert
} from 'lucide-react';
import { api } from '../../services/api';

export default function SettingsView({ currentRole, setCurrentRole }) {
  const [activeTab, setActiveTab] = useState('guardrails'); // 'guardrails' | 'terminology' | 'evaluation'

  // Terminology
  const [terms, setTerms] = useState({
    orgLevel: 'Organization',
    sectorLevel: 'Industry / Sector',
    plantLevel: 'Plant / Site',
    areaLevel: 'Area / Unit',
    assetLevel: 'Asset / Machine'
  });

  // Guardrails
  const [trustedSources, setTrustedSources] = useState({
    approvedOEM: true,
    approvedSOP: true,
    verifiedMaintenance: true,
    verifiedInspection: true,
    verifiedHumanNotes: true,
  });

  const [excludedSources, setExcludedSources] = useState({
    obsoleteDocs: true,
    unverifiedDocs: true,
    draftDocs: true,
  });

  // Benchmark Evaluation State (Moved from operational Knowledge page)
  const [benchmarkResult, setBenchmarkResult] = useState(null);
  const [runningBenchmark, setRunningBenchmark] = useState(false);

  const handleRunBenchmarks = async () => {
    setRunningBenchmark(true);
    try {
      const res = await api.runBenchmarks();
      setBenchmarkResult(res);
    } catch (err) {
      alert('Benchmark evaluation failed: ' + err.message);
    } finally {
      setRunningBenchmark(false);
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      {/* Header & Sub-Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="text-xs font-mono tracking-wider uppercase text-slate-400 font-semibold mb-1">
            System Administration
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Sliders className="w-6 h-6 text-brand-400" />
            <span>Settings & Diagnostics</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Configure agent reasoning boundaries, organizational terminology, and run ground-truth evaluations
          </p>
        </div>

        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-900 border border-slate-800 text-xs font-semibold">
          <button
            onClick={() => setActiveTab('guardrails')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'guardrails' ? 'bg-brand-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            Guardrails
          </button>
          <button
            onClick={() => setActiveTab('terminology')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'terminology' ? 'bg-brand-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            Hierarchy
          </button>
          <button
            onClick={() => setActiveTab('evaluation')}
            className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === 'evaluation' ? 'bg-brand-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Award className="w-3.5 h-3.5 text-amber-400" />
            <span>Evaluation (25 Qs)</span>
          </button>
        </div>
      </div>

      {/* TAB 1: REASONING POLICY & GUARDRAILS */}
      {activeTab === 'guardrails' && (
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-6 shadow-xl">
          <div className="flex items-center gap-2.5 border-b border-slate-800 pb-3">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <div>
              <h3 className="font-bold text-sm text-white">Strict Agent Grounding & Knowledge Boundaries</h3>
              <p className="text-xs text-slate-400">Enforce trusted vs excluded document classifications for AI citations</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
            {/* Trusted Sources */}
            <div className="space-y-3">
              <h4 className="font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                <Check className="w-4 h-4" />
                <span>Trusted Knowledge Sources</span>
              </h4>
              <div className="space-y-2">
                {[
                  { key: 'approvedOEM', label: 'Approved OEM Manuals' },
                  { key: 'approvedSOP', label: 'Current Approved SOPs' },
                  { key: 'verifiedMaintenance', label: 'Verified Maintenance Records' },
                  { key: 'verifiedInspection', label: 'Verified Condition Monitoring Reports' },
                  { key: 'verifiedHumanNotes', label: 'Authorized Operator Field Notes' },
                ].map((item) => (
                  <label key={item.key} className="flex items-center gap-2.5 p-2.5 rounded-xl bg-slate-950 border border-slate-800/80 cursor-pointer hover:border-slate-700">
                    <input
                      type="checkbox"
                      checked={trustedSources[item.key]}
                      onChange={(e) => setTrustedSources({ ...trustedSources, [item.key]: e.target.checked })}
                      className="rounded border-slate-700 text-brand-500 focus:ring-0"
                    />
                    <span className="text-slate-200">{item.label}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Excluded Sources */}
            <div className="space-y-3">
              <h4 className="font-semibold text-red-400 uppercase tracking-wider flex items-center gap-1.5">
                <X className="w-4 h-4" />
                <span>Excluded Sources (Zero Citation)</span>
              </h4>
              <div className="space-y-2">
                {[
                  { key: 'obsoleteDocs', label: 'Obsolete / Superseded Documents' },
                  { key: 'unverifiedDocs', label: 'Unverified Industrial Uploads' },
                  { key: 'draftDocs', label: 'Draft Documents Under Review' },
                ].map((item) => (
                  <label key={item.key} className="flex items-center gap-2.5 p-2.5 rounded-xl bg-slate-950 border border-slate-800/80 cursor-pointer hover:border-slate-700">
                    <input
                      type="checkbox"
                      checked={excludedSources[item.key]}
                      onChange={(e) => setExcludedSources({ ...excludedSources, [item.key]: e.target.checked })}
                      className="rounded border-slate-700 text-red-500 focus:ring-0"
                    />
                    <span className="text-slate-300">{item.label}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-brand-500/20 text-xs space-y-2">
            <span className="font-semibold text-brand-400 flex items-center gap-2">
              <Sparkles className="w-4 h-4" />
              <span>Active Agent Reasoning Constraints:</span>
            </span>
            <ul className="list-disc pl-5 space-y-1 text-slate-300 leading-relaxed">
              <li><strong>Refusal Guardrail:</strong> Returns <em>"I could not find sufficient information in the available industrial records."</em> if citation evidence is absent.</li>
              <li><strong>Mandatory Grounding:</strong> Every claim requires Document ID, Page, and Section.</li>
              <li><strong>Zero Unsupported Causation:</strong> Language restricted to <em>Potential, Observed, Detected, Supported by records</em>.</li>
            </ul>
          </div>
        </div>
      )}

      {/* TAB 2: TERMINOLOGY HIERARCHY */}
      {activeTab === 'terminology' && (
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-5 shadow-xl">
          <div className="flex items-center gap-2.5 border-b border-slate-800 pb-3">
            <Layers className="w-5 h-5 text-cyan-400" />
            <div>
              <h3 className="font-bold text-sm text-white">Configurable Hierarchy Terminology</h3>
              <p className="text-xs text-slate-400">Adapt level naming conventions to match your specific industry domain</p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-xs">
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Level 1 (Top)</label>
              <input
                type="text"
                value={terms.orgLevel}
                onChange={(e) => setTerms({ ...terms, orgLevel: e.target.value })}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Level 2</label>
              <input
                type="text"
                value={terms.sectorLevel}
                onChange={(e) => setTerms({ ...terms, sectorLevel: e.target.value })}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Level 3</label>
              <input
                type="text"
                value={terms.plantLevel}
                onChange={(e) => setTerms({ ...terms, plantLevel: e.target.value })}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Level 4</label>
              <input
                type="text"
                value={terms.areaLevel}
                onChange={(e) => setTerms({ ...terms, areaLevel: e.target.value })}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Level 5 (Central Object)</label>
              <input
                type="text"
                value={terms.assetLevel}
                onChange={(e) => setTerms({ ...terms, assetLevel: e.target.value })}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white font-bold"
              />
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: BENCHMARK EVALUATION (Section 32) */}
      {activeTab === 'evaluation' && (
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-850 to-slate-900 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-mono text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20 font-semibold">
                  Diagnostic Evaluation Suite
                </span>
                <span className="text-xs text-slate-400">• 25 Fixed Questions</span>
              </div>
              <h3 className="text-lg font-bold text-white tracking-tight">
                Industrial Accuracy & Latency Benchmark Harness
              </h3>
              <p className="text-xs text-slate-400 mt-1 max-w-xl">
                Automated evaluation against ground-truth industrial records. Validates answer retrieval, citation precision, and "I Don't Know" refusal protection.
              </p>
            </div>

            <button
              onClick={handleRunBenchmarks}
              disabled={runningBenchmark}
              className="px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold text-xs transition-all flex items-center gap-2 shadow-lg shadow-emerald-500/20 disabled:opacity-50 shrink-0"
            >
              {runningBenchmark ? (
                <RotateCw className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              <span>{runningBenchmark ? 'Evaluating 25 Questions...' : 'Run Benchmark Harness'}</span>
            </button>
          </div>

          {benchmarkResult && (
            <div className="space-y-6 animate-in fade-in duration-200">
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-xs">
                <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                  <span className="text-slate-400 text-[11px]">Overall Accuracy</span>
                  <div className="text-2xl font-bold font-mono text-emerald-400">
                    {benchmarkResult.answer_accuracy_pct}%
                  </div>
                  <div className="text-[10px] text-slate-400">
                    {benchmarkResult.passed_count}/{benchmarkResult.total_questions} Questions Passed
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                  <span className="text-slate-400 text-[11px]">Retrieval Accuracy</span>
                  <div className="text-2xl font-bold font-mono text-cyan-400">
                    {benchmarkResult.retrieval_accuracy_pct}%
                  </div>
                  <div className="text-[10px] text-slate-400">Top chunk ground truth</div>
                </div>

                <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                  <span className="text-slate-400 text-[11px]">Citation Precision</span>
                  <div className="text-2xl font-bold font-mono text-purple-400">
                    {benchmarkResult.citation_accuracy_pct}%
                  </div>
                  <div className="text-[10px] text-slate-400">Exact page & doc cited</div>
                </div>

                <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                  <span className="text-slate-400 text-[11px]">Refusal Protection</span>
                  <div className="text-2xl font-bold font-mono text-brand-400">
                    {benchmarkResult.refusal_accuracy_pct}%
                  </div>
                  <div className="text-[10px] text-slate-400">Zero hallucinations</div>
                </div>

                <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                  <span className="text-slate-400 text-[11px]">Speedup vs Manual</span>
                  <div className="text-2xl font-bold font-mono text-amber-400">
                    {Math.round(benchmarkResult.platform_speedup_factor).toLocaleString()}x
                  </div>
                  <div className="text-[10px] text-slate-400">
                    {benchmarkResult.avg_latency_ms}ms avg latency
                  </div>
                </div>
              </div>

              {/* Questions Breakdown Table */}
              <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                  Test Case Results Breakdown
                </h4>

                <div className="max-h-96 overflow-y-auto pr-1">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400 font-mono text-[11px]">
                        <th className="py-2 px-3">ID</th>
                        <th className="py-2 px-3">Category</th>
                        <th className="py-2 px-3">Question</th>
                        <th className="py-2 px-3">Latency</th>
                        <th className="py-2 px-3 text-right">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                      {benchmarkResult.details.map((d) => (
                        <tr key={d.id} className="hover:bg-slate-800/40">
                          <td className="py-2 px-3 text-brand-400 font-bold">{d.id}</td>
                          <td className="py-2 px-3 text-slate-400">{d.category}</td>
                          <td className="py-2 px-3 text-slate-200 font-sans max-w-xs truncate">{d.question}</td>
                          <td className="py-2 px-3 text-slate-400">{d.latency_ms}ms</td>
                          <td className="py-2 px-3 text-right">
                            <span className={`px-2 py-0.5 rounded font-bold text-[10px] ${
                              d.status === 'PASSED'
                                ? 'bg-emerald-500/20 text-emerald-400'
                                : 'bg-red-500/20 text-red-400'
                            }`}>
                              {d.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
