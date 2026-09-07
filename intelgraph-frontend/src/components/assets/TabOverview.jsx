import React, { useState } from 'react';
import { 
  Sparkles, 
  FileText, 
  ArrowRight, 
  CheckCircle2, 
  AlertTriangle, 
  ChevronDown, 
  ChevronUp, 
  ExternalLink,
  Calendar,
  Layers,
  Wrench,
  Activity
} from 'lucide-react';
import EvidenceDrawer from '../common/EvidenceDrawer';

export default function TabOverview({ asset, maintenanceData, onOpenDocViewer, onOpenSOP }) {
  const [coverageExpanded, setCoverageExpanded] = useState(false);
  const [specsExpanded, setSpecsExpanded] = useState(false);
  const [componentsExpanded, setComponentsExpanded] = useState(false);
  const [evidenceDrawerOpen, setEvidenceDrawerOpen] = useState(false);

  // Verified evidence items for P-101 story
  const verifiedEvidenceList = [
    {
      document_name: 'Pump_P101_OEM_Manual',
      title: 'P-101 Centrifugal Pump Operating Manual',
      document_id: 'Pump_P101_OEM_Manual',
      date: '2023-01-15',
      page: '3',
      section: 'Section 4.2 Vibration Tolerances',
      status: 'Approved',
      governance_status: 'Approved',
      technician: 'Flowserve Engineering',
      excerpt: 'Normal operating vibration RMS velocity limit is 4.5 mm/s. Shutdown threshold is 9.0 mm/s. Radial ball bearing clearance must be inspected every 4,000 hrs.'
    },
    {
      document_name: 'P101_Inspection_Report_Aug_2025',
      title: 'Vibration Analysis & Condition Report',
      document_id: 'P101_Inspection_Report_Aug_2025',
      date: '2025-08-15',
      page: '1',
      section: 'Bearing Velocity Survey',
      status: 'Verified',
      governance_status: 'Verified',
      technician: 'R. Davis (Condition Analyst)',
      excerpt: 'Drive-End bearing measured 6.8 mm/s RMS vibration velocity, exceeding normal warning limit of 4.5 mm/s. Noted elevated 2x line frequency harmonic peaks.'
    },
    {
      document_name: 'P101_Failure_Report_Feb_2026',
      title: 'Unscheduled Seizure Trip & RCA Report',
      document_id: 'P101_Failure_Report_Feb_2026',
      date: '2026-02-22',
      page: '1',
      section: 'Root Cause Findings',
      status: 'Verified',
      governance_status: 'Verified',
      technician: 'K. Patel (Maintenance Lead)',
      excerpt: 'Failure Mode: Drive-End Bearing Seizure. Ball cage disintegration caused by long-term cyclic fatigue and inadequate lubrication film under elevated temperature.'
    }
  ];

  // Visual Timeline points
  const timelinePoints = [
    {
      year: '2024',
      title: 'Bearing replaced',
      tag: 'WO-1023',
      note: 'Routine preventive overhaul, SKF 6312 installed'
    },
    {
      year: '2025',
      title: 'Elevated vibration observed',
      tag: 'INSP-456',
      note: '6.8 mm/s RMS (exceeded 4.5 mm/s warning threshold)'
    },
    {
      year: '2026',
      title: 'Bearing seizure recorded',
      tag: 'WO-1189',
      note: 'Drive-end bearing seizure trip; 18.5h downtime'
    }
  ];

  // 8 Knowledge Areas Breakdown (Explainable)
  const knowledgePillars = [
    { name: 'OEM Documentation', status: 'available', detail: 'Approved technical manual on file' },
    { name: 'SOP', status: 'available', detail: 'SOP-101-M Bearing Maintenance approved' },
    { name: 'Maintenance History', status: 'available', detail: 'WO-1023, WO-1189 verified records' },
    { name: 'Inspection Records', status: 'available', detail: 'INSP-456 vibration survey verified' },
    { name: 'Failure History', status: 'available', detail: 'Incident #78 failure report verified' },
    { name: 'Component Registry', status: 'available', detail: 'SKF 6312, Impeller, Mechanical Seal registered' },
    { name: 'Telemetry Stream', status: 'available', detail: 'Continuous vibration and temperature stream active' },
    { name: 'Calibration Records', status: 'missing', detail: 'PT-101 transmitter calibration certificate missing' },
  ];

  const availableCount = knowledgePillars.filter(p => p.status === 'available').length;

  return (
    <div className="space-y-6">
      {/* 1. TOP SECTION: AI ASSET SUMMARY (Purple Accent) */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-purple-950/25 via-slate-900 to-slate-900 border border-purple-500/30 space-y-4 shadow-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="p-1 rounded bg-purple-500/20 text-purple-400">
              <Sparkles className="w-4 h-4" />
            </span>
            <span className="text-[11px] font-mono uppercase tracking-wider text-purple-300 font-semibold">
              AI Asset Summary
            </span>
          </div>
          <span className="text-[11px] font-mono text-emerald-400 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Grounded in approved records</span>
          </span>
        </div>

        {/* Headline */}
        <h2 className="text-base font-bold text-white tracking-tight">
          "Potential recurring bearing-related issue is supported by three historical records."
        </h2>

        {/* WHY THIS MATTERS */}
        <div className="space-y-1">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
            Why This Matters
          </div>
          <p className="text-xs text-slate-300 leading-relaxed max-w-3xl">
            Recurring mechanical stress on the drive-end bearing without root-cause correction creates a high probability of another unpredicted trip, resulting in production downtime.
          </p>
        </div>

        {/* SIMPLE VISUAL TIMELINE */}
        <div className="pt-2">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold mb-3">
            Historical Progression Timeline
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {timelinePoints.map((item, idx) => (
              <div 
                key={idx}
                className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1 relative"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-sm font-bold text-purple-400">
                    {item.year}
                  </span>
                  <span className="text-[10px] font-mono text-slate-400 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">
                    {item.tag}
                  </span>
                </div>
                <div className="font-semibold text-xs text-white">
                  {item.title}
                </div>
                <div className="text-[11px] text-slate-400">
                  {item.note}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* EVIDENCE & RECOMMENDED REVIEW ACTIONS */}
        <div className="pt-3 border-t border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-300">
              <strong className="text-white">Evidence:</strong> 3 verified records
            </span>
            <button
              onClick={() => setEvidenceDrawerOpen(true)}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-brand-400 hover:text-brand-300 font-semibold text-xs border border-slate-700 transition-all flex items-center gap-1.5"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>View Evidence</span>
            </button>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-300">
              <strong className="text-white">Recommended Review:</strong> Review applicable bearing procedure
            </span>
            <button
              onClick={() => onOpenDocViewer ? onOpenDocViewer('SOP-101_Centrifugal_Pump_Operation') : alert('Opening SOP-101-M...')}
              className="px-3.5 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs shadow-md shadow-purple-600/20 transition-all flex items-center gap-1.5"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span>Open SOP</span>
            </button>
          </div>
        </div>
      </div>

      {/* 2. KNOWLEDGE COVERAGE (Progressive Disclosure & Explainable) */}
      <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
              Knowledge Coverage
            </div>
            <div className="text-sm font-bold text-white mt-0.5">
              {availableCount} / {knowledgePillars.length} knowledge areas available
            </div>
          </div>

          <button
            onClick={() => setCoverageExpanded(!coverageExpanded)}
            className="text-xs text-brand-400 hover:text-brand-300 font-medium flex items-center gap-1"
          >
            <span>{coverageExpanded ? 'Collapse Coverage' : 'Expand Breakdown'}</span>
            {coverageExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>

        {/* Restrained Progress Bar */}
        <div className="w-full h-2 rounded-full bg-slate-950 border border-slate-800 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-brand-500 to-cyan-400 rounded-full"
            style={{ width: `${(availableCount / knowledgePillars.length) * 100}%` }}
          />
        </div>

        {/* Explainable Breakdown Checklist (Expanded) */}
        {coverageExpanded && (
          <div className="pt-3 border-t border-slate-800 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5 text-xs animate-in fade-in duration-150">
            {knowledgePillars.map((p, idx) => (
              <div
                key={idx}
                className={`p-2.5 rounded-lg border ${
                  p.status === 'available'
                    ? 'bg-slate-950/60 border-slate-800 text-slate-300'
                    : 'bg-amber-950/20 border-amber-500/30 text-amber-200'
                }`}
              >
                <div className="flex items-center justify-between font-semibold">
                  <span>{p.name}</span>
                  {p.status === 'available' ? (
                    <span className="text-emerald-400 font-bold">✓</span>
                  ) : (
                    <span className="text-amber-400 font-bold">⚠ Missing</span>
                  )}
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">{p.detail}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 3. SECONDARY SECTIONS: SPECIFICATIONS & REGISTERED COMPONENTS */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Key Specifications (Collapsible) */}
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Key Specifications
            </h3>
            <button
              onClick={() => setSpecsExpanded(!specsExpanded)}
              className="text-xs text-slate-400 hover:text-white flex items-center gap-1"
            >
              <span>{specsExpanded ? 'Hide' : 'Show Details'}</span>
              {specsExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
          </div>

          <div className="space-y-1.5 text-xs font-mono">
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Maker / Model:</span>
              <span className="text-slate-200 font-semibold">{asset.manufacturer} {asset.model}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Design Flow / Head:</span>
              <span className="text-slate-200">180 m³/h @ 45m TDH</span>
            </div>

            {specsExpanded && (
              <>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Operating Speed:</span>
                  <span className="text-slate-200">2950 RPM (75 kW Motor)</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Serial Number:</span>
                  <span className="text-slate-200">{asset.serial_number}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">Approved Lubricant:</span>
                  <span className="text-emerald-400 font-bold">ISO VG 46 Synthetic</span>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Registered Components (Collapsible) */}
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Components ({asset.components?.length || 0})
            </h3>
            <button
              onClick={() => setComponentsExpanded(!componentsExpanded)}
              className="text-xs text-slate-400 hover:text-white flex items-center gap-1"
            >
              <span>{componentsExpanded ? 'Hide' : 'Show All'}</span>
              {componentsExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
          </div>

          <div className="space-y-1.5 text-xs">
            {asset.components?.slice(0, componentsExpanded ? asset.components.length : 2).map((c) => (
              <div key={c.id} className="p-2 rounded bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
                <div>
                  <span className="font-semibold text-white">{c.name}</span>
                  <span className="text-[11px] text-slate-400 font-mono ml-2">({c.part_number || 'OEM Standard'})</span>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-mono">
                  {c.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Evidence Traceability Drawer */}
      <EvidenceDrawer
        isOpen={evidenceDrawerOpen}
        onClose={() => setEvidenceDrawerOpen(false)}
        evidenceData={verifiedEvidenceList}
        onOpenDocViewer={onOpenDocViewer}
      />
    </div>
  );
}
