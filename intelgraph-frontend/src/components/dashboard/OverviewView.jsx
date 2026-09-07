import React, { useState } from 'react';
import { 
  Cpu, 
  AlertCircle, 
  ArrowRight, 
  Sparkles, 
  ShieldAlert, 
  Clock, 
  CheckCircle2, 
  ChevronDown, 
  ChevronUp,
  FileText
} from 'lucide-react';
import EvidenceDrawer from '../common/EvidenceDrawer';

export default function OverviewView({ 
  overviewData, 
  currentRole, 
  onSelectAsset, 
  onNavigate 
}) {
  const [expandedActionId, setExpandedActionId] = useState(null);
  const [evidenceDrawerOpen, setEvidenceDrawerOpen] = useState(false);
  const [selectedEvidence, setSelectedEvidence] = useState(null);

  if (!overviewData) {
    return (
      <div className="p-16 text-center text-slate-400">
        <div className="w-8 h-8 border-2 border-brand-400 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
        Synthesizing operational fleet status...
      </div>
    );
  }

  const { metrics, open_findings, cross_asset_alerts } = overviewData;

  // Curated Operational Priority Queue based on verified backend records
  const priorityItems = [
    {
      id: 'act-c201-overhaul',
      severity: 'CRITICAL',
      assetTag: 'C-201',
      title: 'Overhaul overdue',
      signal: '4 days beyond scheduled interval.',
      why: 'Operating hours (24,500 hrs) exceeded the major overhaul threshold (24,000 hrs).',
      evidence: 'WO-2010 (Scheduled Overhaul Window: Aug 2026)',
      evidenceList: [
        {
          document_name: 'C201_Maintenance_Schedule',
          date: '2026-08-01',
          page: '1',
          status: 'Verified',
          excerpt: 'Major overhaul interval specified at 24,000 running hours. Immediate inspection required if threshold exceeded.'
        }
      ],
      action: 'Schedule immediate maintenance overhaul window.',
      owner: 'Maintenance Lead'
    },
    {
      id: 'act-p101-bearing',
      severity: 'HIGH',
      assetTag: 'P-101',
      title: 'Potential recurring bearing-related issue',
      signal: '3 supporting historical records.',
      why: 'Drive-end bearing replaced in 2024, elevated vibration observed in 2025, and seizure trip recorded in Feb 2026.',
      evidence: 'WO-1023, INSP-456, WO-1189',
      evidenceList: [
        {
          document_name: 'Pump_P101_OEM_Manual',
          date: '2023-01-15',
          page: '3',
          status: 'Approved',
          excerpt: 'Vibration velocity warning threshold: 4.5 mm/s RMS. Radial clearance limit: 0.05 mm.'
        },
        {
          document_name: 'P101_Inspection_Report_Aug_2025',
          date: '2025-08-15',
          page: '1',
          status: 'Verified',
          excerpt: 'Measured vibration: 6.8 mm/s RMS on drive-end bearing, exceeding warning threshold.'
        },
        {
          document_name: 'P101_Failure_Report_Feb_2026',
          date: '2026-02-22',
          page: '1',
          status: 'Verified',
          excerpt: 'Unscheduled trip caused by drive-end bearing seizure. Fatigue initiated by chronic vibration.'
        }
      ],
      action: 'Review applicable approved bearing inspection and lubrication procedure (SOP-101-M).',
      owner: 'Reliability Engineer'
    },
    {
      id: 'act-p101-calibration',
      severity: 'MEDIUM',
      assetTag: 'P-101',
      title: 'Calibration evidence missing',
      signal: 'Pressure transmitter PT-101 calibration certificate unverified.',
      why: 'Annual instrumentation audit requires verified calibration documentation for discharge safety loop.',
      evidence: 'Audit GAP-101-CAL',
      evidenceList: [
        {
          document_name: 'Instrumentation_Compliance_Matrix',
          date: '2026-06-01',
          page: '4',
          status: 'Audit Gap',
          excerpt: 'Pressure transmitter PT-101 calibration interval: 12 months. Current record expired.'
        }
      ],
      action: 'Upload calibration certificate or schedule recalibration test.',
      owner: 'Instrumentation Tech'
    }
  ];

  // Compact Asset Health Registry
  const assetsHealthList = [
    {
      tag: 'P-101',
      name: 'Centrifugal Water Injection Pump',
      status: 'Operational',
      statusColor: 'emerald',
      issue: '1 issue requiring review (Potential recurring bearing issue)',
      nextMaintenance: '12 Sep 2026',
      knowledgeCoverage: '7/8'
    },
    {
      tag: 'C-201',
      name: 'Reciprocating Gas Compressor',
      status: 'Attention',
      statusColor: 'red',
      issue: 'Overhaul overdue (4 days beyond interval)',
      nextMaintenance: 'Overdue (Immediate)',
      knowledgeCoverage: '5/8'
    },
    {
      tag: 'P-102',
      name: 'Centrifugal Booster Pump (Standby)',
      status: 'Operational',
      statusColor: 'emerald',
      issue: 'Standby pump — all condition parameters nominal',
      nextMaintenance: '28 Oct 2026',
      knowledgeCoverage: '6/8'
    },
    {
      tag: 'P-205',
      name: 'Slurry Transfer Pump',
      status: 'Operational',
      statusColor: 'emerald',
      issue: 'Day-1 registration complete — baseline established',
      nextMaintenance: '15 Nov 2026',
      knowledgeCoverage: '4/8'
    }
  ];

  const handleOpenEvidence = (item) => {
    setSelectedEvidence(item.evidenceList);
    setEvidenceDrawerOpen(true);
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      {/* 1. PLANT OPERATIONAL ATTENTION HEADER */}
      <div className="border-b border-slate-800 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="text-xs font-mono tracking-wider uppercase text-slate-400 font-semibold mb-1">
            Site Facility Status
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            PLANT A
          </h1>
          <div className="flex flex-wrap items-center gap-4 text-xs mt-2">
            <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              4 operational
            </span>
            <span className="text-slate-400">•</span>
            <span className="flex items-center gap-1.5 text-red-400 font-medium">
              <span className="w-2 h-2 rounded-full bg-red-400"></span>
              1 critical action
            </span>
            <span className="text-slate-400">•</span>
            <span className="flex items-center gap-1.5 text-amber-400 font-medium">
              <span className="w-2 h-2 rounded-full bg-amber-400"></span>
              3 items requiring review
            </span>
          </div>
        </div>

        <div className="text-right hidden sm:block font-mono text-xs text-slate-400">
          <span className="text-slate-400">Perspective:</span>{' '}
          <span className="text-brand-400 font-semibold">{currentRole}</span>
        </div>
      </div>

      {/* 2. FLEET CROSS-ASSET INTELLIGENCE (Compact & Actionable) */}
      {cross_asset_alerts && cross_asset_alerts.length > 0 && (
        <div className="p-4 rounded-xl bg-purple-950/20 border border-purple-500/30 flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <Sparkles className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-purple-200">
                  Cross-Asset Intelligence Detected: {cross_asset_alerts[0].pattern_title}
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-500/20 text-purple-300">
                  Affected: {cross_asset_alerts[0].affected_assets.join(', ')}
                </span>
              </div>
              <p className="text-xs text-slate-300 mt-1">
                {cross_asset_alerts[0].summary}
              </p>
            </div>
          </div>
          <button
            onClick={() => onNavigate('reports')}
            className="text-xs font-semibold text-purple-300 hover:text-purple-100 flex items-center gap-1 whitespace-nowrap pt-0.5 transition-colors"
          >
            <span>RCA Report</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* 3. NEEDS ATTENTION — HIGH-PRIORITY OPERATIONAL QUEUE */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
            <span>Needs Operational Attention</span>
            <span className="text-xs font-mono font-normal text-slate-400">({priorityItems.length} priority items)</span>
          </h2>
          <button
            onClick={() => onNavigate('actions')}
            className="text-xs text-brand-400 hover:text-brand-300 font-medium flex items-center gap-1 transition-colors"
          >
            <span>View Action Center</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        </div>

        {/* Role Operational Perspective Banner */}
        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2 font-mono">
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Perspective:</span>
            <span className="text-brand-400 font-bold px-2 py-0.5 rounded bg-brand-500/10 border border-brand-500/20">{currentRole}</span>
          </div>
          <span className="text-slate-300 text-[11px]">
            {currentRole === 'Quality / Compliance User' 
              ? 'Auditing Mode: Prioritizing regulatory standards, calibration evidence gaps & document governance.'
              : currentRole === 'Plant Manager'
              ? 'Executive Mode: Prioritizing fleet availability (4/5 active), downtime risks & cross-asset anomalies.'
              : 'Engineering Mode: Prioritizing component health, overdue work orders & vibration alarm limits.'}
          </span>
        </div>

        <div className="space-y-2.5">
          {(currentRole === 'Quality / Compliance User' 
            ? [priorityItems[2], priorityItems[0], priorityItems[1]]
            : currentRole === 'Plant Manager'
            ? [priorityItems[0], priorityItems[1], priorityItems[2]]
            : priorityItems
          ).map((item) => {
            const isExpanded = expandedActionId === item.id;
            const isCrit = item.severity === 'CRITICAL';
            const isHigh = item.severity === 'HIGH';

            return (
              <div
                key={item.id}
                className={`rounded-xl border transition-all ${
                  isCrit
                    ? 'bg-red-950/15 border-red-500/30'
                    : isHigh
                    ? 'bg-amber-950/15 border-amber-500/30'
                    : 'bg-slate-900 border-slate-800'
                }`}
              >
                {/* Collapsed Bar (Headline -> Signal -> Quick Review) */}
                <div className="p-4 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 min-w-0">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                      isCrit
                        ? 'bg-red-500/20 text-red-400'
                        : isHigh
                        ? 'bg-amber-500/20 text-amber-400'
                        : 'bg-blue-500/20 text-blue-400'
                    }`}>
                      {item.severity}
                    </span>

                    <button
                      onClick={() => onSelectAsset(item.assetTag)}
                      className="font-mono font-bold text-xs text-white hover:text-brand-400 transition-colors"
                    >
                      {item.assetTag}
                    </button>

                    <span className="text-slate-400 text-xs hidden sm:inline">•</span>

                    <span className="font-semibold text-xs text-slate-200 truncate">
                      {item.title}
                    </span>

                    <span className="text-slate-400 text-xs hidden md:inline truncate">
                      — {item.signal}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => setExpandedActionId(isExpanded ? null : item.id)}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-all flex items-center gap-1"
                    >
                      <span>{isExpanded ? 'Collapse' : 'Review'}</span>
                      {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>

                {/* Expanded State (Progressive Disclosure) */}
                {isExpanded && (
                  <div className="px-5 pb-5 pt-1 border-t border-slate-800/80 space-y-4 text-xs animate-in fade-in duration-150">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
                      <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800">
                        <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block mb-1">
                          Why This Matters
                        </span>
                        <p className="text-slate-300 leading-relaxed">{item.why}</p>
                      </div>

                      <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800">
                        <span className="text-[10px] font-mono uppercase tracking-wider text-brand-400 font-semibold block mb-1">
                          Required Operational Action
                        </span>
                        <p className="text-slate-200 leading-relaxed font-medium">{item.action}</p>
                      </div>

                      <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800 flex flex-col justify-between">
                        <div>
                          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block mb-1">
                            Supporting Records
                          </span>
                          <p className="text-slate-300 font-mono text-[11px]">{item.evidence}</p>
                        </div>
                        <div className="pt-2 flex items-center justify-between text-[11px] text-slate-400">
                          <span>Owner: <strong className="text-slate-200">{item.owner}</strong></span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-1">
                      <button
                        onClick={() => handleOpenEvidence(item)}
                        className="text-xs text-brand-400 hover:text-brand-300 font-medium flex items-center gap-1.5 transition-colors"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        <span>View Evidence Chain</span>
                      </button>

                      <button
                        onClick={() => onSelectAsset(item.assetTag)}
                        className="px-3.5 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white font-semibold text-xs flex items-center gap-1.5 transition-all shadow-md shadow-brand-500/20"
                      >
                        <span>Open Machine Brain ({item.assetTag})</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* 4. ASSET HEALTH — COMPACT OPERATIONAL ROWS */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
            Asset Health
          </h2>
          <button
            onClick={() => onNavigate('assets')}
            className="text-xs text-brand-400 hover:text-brand-300 font-medium flex items-center gap-1 transition-colors"
          >
            <span>All Machinery ({assetsHealthList.length})</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        </div>

        <div className="space-y-2">
          {assetsHealthList.map((mach) => (
            <div
              key={mach.tag}
              className="p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition-all"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-3">
                  <span className="font-mono font-bold text-sm text-white">
                    {mach.tag}
                  </span>
                  <span className="text-xs font-semibold text-slate-300">
                    {mach.name}
                  </span>
                  <span className="flex items-center gap-1 text-xs">
                    <span className={`w-2 h-2 rounded-full ${
                      mach.statusColor === 'emerald' ? 'bg-emerald-400' : 'bg-red-400 animate-pulse'
                    }`}></span>
                    <span className={mach.statusColor === 'emerald' ? 'text-emerald-400' : 'text-red-400 font-semibold'}>
                      {mach.status}
                    </span>
                  </span>
                </div>

                <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                  <span className={mach.statusColor === 'red' ? 'text-red-300 font-medium' : 'text-slate-400'}>
                    {mach.issue}
                  </span>
                  <span>•</span>
                  <span>Next maintenance: <strong className="text-slate-300">{mach.nextMaintenance}</strong></span>
                  <span>•</span>
                  <span className="font-mono text-[11px] text-slate-400">Knowledge: {mach.knowledgeCoverage}</span>
                </div>
              </div>

              <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                <button
                  onClick={() => onSelectAsset(mach.tag)}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1 ${
                    mach.status === 'Attention'
                      ? 'bg-red-500/20 hover:bg-red-500/30 text-red-300 border border-red-500/30'
                      : 'bg-slate-800 hover:bg-slate-750 text-brand-400 border border-slate-700/80'
                  }`}
                >
                  <span>{mach.status === 'Attention' ? 'Review' : 'Open Asset'}</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Reusable Evidence Traceability Drawer */}
      <EvidenceDrawer
        isOpen={evidenceDrawerOpen}
        onClose={() => setEvidenceDrawerOpen(false)}
        evidenceData={selectedEvidence}
      />
    </div>
  );
}
