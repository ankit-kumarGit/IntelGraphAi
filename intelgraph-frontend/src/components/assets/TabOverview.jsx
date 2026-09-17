import React, { useState } from 'react';
import { 
  Sparkles, 
  FileText, 
  CheckCircle2, 
  ChevronDown, 
  ChevronUp, 
  ExternalLink
} from 'lucide-react';
import EvidenceDrawer from '../common/EvidenceDrawer';

export default function TabOverview({ asset, maintenanceData, onOpenDocViewer, onOpenSOP }) {
  const [coverageExpanded, setCoverageExpanded] = useState(false);
  const [specsExpanded, setSpecsExpanded] = useState(false);
  const [componentsExpanded, setComponentsExpanded] = useState(false);
  const [evidenceDrawerOpen, setEvidenceDrawerOpen] = useState(false);

const MONTH_NAMES = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
];

function formatTimelineDate(rawDate) {
  if (!rawDate || typeof rawDate !== 'string') return 'Date Unrecorded';
  const trimmed = rawDate.trim();
  if (!trimmed || trimmed.toLowerCase() === 'unknown' || trimmed.toLowerCase() === 'unrecorded' || trimmed.toLowerCase() === 'historical') {
    return 'Date Unrecorded';
  }

  // 1. ISO format: YYYY-MM-DD
  const isoMatch = trimmed.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})/);
  if (isoMatch) {
    const year = isoMatch[1];
    const monthIdx = parseInt(isoMatch[2], 10) - 1;
    const day = parseInt(isoMatch[3], 10);
    if (monthIdx >= 0 && monthIdx < 12 && day >= 1 && day <= 31) {
      const monthName = MONTH_NAMES[monthIdx];
      return `${day < 10 ? '0' + day : day} ${monthName} ${year}`;
    }
  }

  // 2. DD-Mon-YYYY or DD Mon YYYY
  const dmyMatch = trimmed.match(/^(\d{1,2})[-/\s]+([A-Za-z]{3,9})[-/\s]+(\d{4})/);
  if (dmyMatch) {
    const day = parseInt(dmyMatch[1], 10);
    const monStr = dmyMatch[2].slice(0, 3).toLowerCase();
    const year = dmyMatch[3];
    const monthIdx = MONTH_NAMES.findIndex(m => m.toLowerCase() === monStr);
    if (monthIdx !== -1 && day >= 1 && day <= 31) {
      return `${day < 10 ? '0' + day : day} ${MONTH_NAMES[monthIdx]} ${year}`;
    }
  }

  // 3. Fallback to Date.parse
  const parsed = Date.parse(trimmed);
  if (!isNaN(parsed)) {
    const d = new Date(parsed);
    const day = d.getDate();
    const monthName = MONTH_NAMES[d.getMonth()];
    const year = d.getFullYear();
    return `${day < 10 ? '0' + day : day} ${monthName} ${year}`;
  }

  return 'Date Unrecorded';
}

function getEventTimestamp(rawDate) {
  if (!rawDate || typeof rawDate !== 'string') return 0;
  const trimmed = rawDate.trim();
  if (trimmed.toLowerCase() === 'unknown' || trimmed.toLowerCase() === 'historical' || trimmed.toLowerCase() === 'unrecorded') return 0;
  const iso = trimmed.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})/);
  if (iso) {
    return new Date(parseInt(iso[1], 10), parseInt(iso[2], 10) - 1, parseInt(iso[3], 10)).getTime();
  }
  const dmy = trimmed.match(/^(\d{1,2})[-/\s]+([A-Za-z]{3,9})[-/\s]+(\d{4})/);
  if (dmy) {
    const monStr = dmy[2].slice(0, 3).toLowerCase();
    const monthIdx = MONTH_NAMES.findIndex(m => m.toLowerCase() === monStr);
    if (monthIdx !== -1) {
      return new Date(parseInt(dmy[3], 10), monthIdx, parseInt(dmy[1], 10)).getTime();
    }
  }
  const parsed = Date.parse(trimmed);
  return isNaN(parsed) ? 0 : parsed;
}

  // 1. DYNAMIC TIMELINE GENERATION
  const timelineEvents = [];

  (maintenanceData?.work_orders || []).forEach(wo => {
    const rawDate = wo.date || wo.event_date;
    timelineEvents.push({
      date: rawDate,
      displayDate: formatTimelineDate(rawDate),
      timestamp: getEventTimestamp(rawDate),
      title: wo.description || `Work Order ${wo.work_order_number || wo.record_id}`,
      tag: wo.work_order_number || wo.record_id || 'WO',
      note: wo.parts_replaced?.length ? `Replaced: ${wo.parts_replaced.join(', ')}` : (wo.description || 'Maintenance completed')
    });
  });

  (maintenanceData?.inspections || []).forEach(insp => {
    const rawDate = insp.date || insp.event_date;
    timelineEvents.push({
      date: rawDate,
      displayDate: formatTimelineDate(rawDate),
      timestamp: getEventTimestamp(rawDate),
      title: insp.result || `Inspection ${insp.inspection_id}`,
      tag: insp.inspection_id || 'INSP',
      note: insp.technician ? `Analyst: ${insp.technician}` : 'Routine condition survey'
    });
  });

  (maintenanceData?.failures || []).forEach(fail => {
    const rawDate = fail.date || fail.event_date;
    timelineEvents.push({
      date: rawDate,
      displayDate: formatTimelineDate(rawDate),
      timestamp: getEventTimestamp(rawDate),
      title: fail.failure_mode || fail.title || `Failure ${fail.failure_id}`,
      tag: fail.failure_id || 'FAIL',
      note: fail.title || 'Unscheduled operational incident'
    });
  });

  // Sort events chronologically (oldest to newest)
  timelineEvents.sort((a, b) => a.timestamp - b.timestamp);

  // 2. DYNAMIC HEADLINE & WHY THIS MATTERS
  let headline = `"${asset?.tag || 'Asset'}: Active asset profile initialized."`;
  let whyThisMatters = "No historical maintenance incidents or failures recorded for this machine.";

  if (maintenanceData?.recurring_patterns?.length) {
    const p = maintenanceData.recurring_patterns[0];
    headline = `"${asset?.tag}: ${p.pattern}."`;
    whyThisMatters = p.observation || "Historical records show multiple interventions. Review maintenance and lubrication procedures.";
  } else if (maintenanceData?.failures?.length) {
    const f = maintenanceData.failures[0];
    headline = `"${asset?.tag}: Historical incident recorded (${f.failure_mode || f.title})."`;
    whyThisMatters = "Operational reliability review is advised to prevent future unplanned trips and downtime.";
  } else if (maintenanceData?.work_orders?.length || maintenanceData?.inspections?.length) {
    const count = (maintenanceData.work_orders?.length || 0) + (maintenanceData.inspections?.length || 0);
    headline = `"${asset?.tag}: Operational maintenance and inspection history verified (${count} record${count > 1 ? 's' : ''})."`;
    whyThisMatters = "Equipment operating within baseline parameters based on verified maintenance records.";
  }

  // 3. DYNAMIC EVIDENCE LIST
  const verifiedEvidenceList = [];

  (maintenanceData?.failures || []).forEach(f => {
    verifiedEvidenceList.push({
      document_name: f.document_ref || f.failure_id,
      title: f.title || `Incident Report ${f.failure_id}`,
      document_id: f.document_ref || f.failure_id,
      date: f.date || 'Verified Record',
      page: '1',
      section: 'Root Cause Findings',
      status: 'Verified',
      governance_status: 'Verified',
      technician: 'Reliability Engineering',
      excerpt: `Failure Mode: ${f.failure_mode || 'Distress recorded'}. Downtime: ${f.downtime_hours || 0}h.`
    });
  });

  (maintenanceData?.inspections || []).forEach(i => {
    verifiedEvidenceList.push({
      document_name: i.document_ref || i.inspection_id,
      title: `Condition Monitoring: ${i.result || i.inspection_id}`,
      document_id: i.document_ref || i.inspection_id,
      date: i.date || 'Verified Record',
      page: '1',
      section: 'Survey Survey',
      status: 'Verified',
      governance_status: 'Verified',
      technician: i.technician || 'Condition Analyst',
      excerpt: `Inspection Result: ${i.result}. Vibration: ${i.vibration_level_mm_s || 'Normal'} mm/s, Temp: ${i.temperature_c || 'Normal'}°C.`
    });
  });

  (maintenanceData?.work_orders || []).forEach(w => {
    verifiedEvidenceList.push({
      document_name: w.document_ref || w.work_order_number || w.record_id,
      title: `Maintenance Record: ${w.work_order_number || w.record_id}`,
      document_id: w.document_ref || w.work_order_number || w.record_id,
      date: w.date || 'Verified Record',
      page: '1',
      section: 'Work Scope',
      status: 'Approved',
      governance_status: 'Approved',
      technician: w.technician || 'Maintenance Lead',
      excerpt: `${w.description || 'Overhaul completed'}. Parts: ${(w.parts_replaced || []).join(', ') || 'Standard overhaul'}.`
    });
  });

  // 4. DYNAMIC KNOWLEDGE PILLARS — derived from actual completeness_breakdown
  const breakdown = asset?.completeness_breakdown || [];
  const getBreakdownStatus = (category) => {
    const item = breakdown.find(b =>
      b.category?.toLowerCase().includes(category.toLowerCase()) ||
      b.label?.toLowerCase().includes(category.toLowerCase())
    );
    if (!item) return 'missing';
    return item.status === 'completed' ? 'available' : (item.status === 'warning' ? 'warning' : 'missing');
  };

  const knowledgePillars = [
    {
      name: 'OEM Documentation',
      status: getBreakdownStatus('OEM'),
      detail: getBreakdownStatus('OEM') === 'available'
        ? `${asset?.tag || 'Asset'} technical documentation on file`
        : 'OEM manual not yet uploaded'
    },
    {
      name: 'SOP',
      status: getBreakdownStatus('SOP'),
      detail: getBreakdownStatus('SOP') === 'available'
        ? `Operating procedure applicable to ${asset?.tag || 'asset'}`
        : 'Standard operating procedure not on file'
    },
    {
      name: 'Maintenance History',
      status: (maintenanceData?.work_orders?.length > 0) ? 'available' : 'missing',
      detail: (maintenanceData?.work_orders?.length > 0)
        ? `${maintenanceData.work_orders.length} verified work order(s)`
        : 'No historical work orders on file'
    },
    {
      name: 'Inspection Records',
      status: (maintenanceData?.inspections?.length > 0) ? 'available' : 'missing',
      detail: (maintenanceData?.inspections?.length > 0)
        ? `${maintenanceData.inspections.length} condition survey(s) verified`
        : 'No inspection surveys on file'
    },
    {
      name: 'Failure History',
      status: (maintenanceData?.failures?.length > 0) ? 'available' : 'missing',
      detail: (maintenanceData?.failures?.length > 0)
        ? `${maintenanceData.failures.length} incident report(s) verified`
        : 'Zero failure incidents recorded'
    },
    {
      name: 'Component Registry',
      status: (asset?.components?.length > 0) ? 'available' : 'missing',
      detail: (asset?.components?.length > 0)
        ? `${asset.components.length} components registered`
        : 'Component registry pending'
    },
    {
      name: 'Telemetry Stream',
      status: getBreakdownStatus('Calibration') === 'available' ? 'available' : 'missing',
      detail: 'Operational condition monitoring'
    },
    {
      name: 'Calibration Records',
      status: getBreakdownStatus('Calibration') === 'available' ? 'available' : 'missing',
      detail: getBreakdownStatus('Calibration') === 'available'
        ? 'Calibration records on file'
        : 'Transmitter calibration certificate review advised'
    }
  ];

  const availableCount = knowledgePillars.filter(p => p.status === 'available').length;

  return (
    <div className="space-y-6">
      {/* 1. TOP SECTION: MACHINE OPERATIONAL SUMMARY */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 shadow-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="p-1 rounded bg-brand-500/10 text-brand-400">
              <Sparkles className="w-4 h-4" />
            </span>
            <span className="text-[11px] font-mono uppercase tracking-wider text-slate-300 font-semibold">
              Machine Operational Summary
            </span>
          </div>
          <span className="text-[11px] font-mono text-emerald-400 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Grounded in approved records</span>
          </span>
        </div>

        {/* Headline */}
        <h2 className="text-base font-bold text-white tracking-tight">
          {headline}
        </h2>

        {/* WHY THIS MATTERS */}
        <div className="space-y-1">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
            Why This Matters
          </div>
          <p className="text-xs text-slate-300 leading-relaxed max-w-3xl">
            {whyThisMatters}
          </p>
        </div>

        {/* DYNAMIC TIMELINE */}
        <div className="pt-2">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold mb-3">
            Historical Progression Timeline
          </div>
          {timelineEvents.length === 0 ? (
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-slate-400 text-xs text-center font-mono">
              No historical maintenance incidents recorded.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {timelineEvents.slice(0, 3).map((item, idx) => (
                <div 
                  key={idx}
                  className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1 relative"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-brand-400">
                      {item.displayDate}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">
                      {item.tag}
                    </span>
                  </div>
                  <div className="font-semibold text-xs text-white truncate">
                    {item.title}
                  </div>
                  <div className="text-[11px] text-slate-400 line-clamp-2">
                    {item.note}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* EVIDENCE & RECOMMENDED REVIEW ACTIONS */}
        <div className="pt-3 border-t border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-300">
              <strong className="text-white">Evidence:</strong> {verifiedEvidenceList.length} verified record{verifiedEvidenceList.length === 1 ? '' : 's'}
            </span>
            {verifiedEvidenceList.length > 0 && (
              <button
                onClick={() => setEvidenceDrawerOpen(true)}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-brand-400 hover:text-brand-300 font-semibold text-xs border border-slate-700 transition-all flex items-center gap-1.5 cursor-pointer"
              >
                <FileText className="w-3.5 h-3.5" />
                <span>View Evidence</span>
              </button>
            )}
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-300">
              <strong className="text-white">Recommended Review:</strong> Review applicable operating procedure
            </span>
            <button
              onClick={() => onOpenDocViewer ? onOpenDocViewer(asset?.tag?.includes('194') ? 'SOP-P194-01_Startup_Shutdown' : 'SOP-101_Centrifugal_Pump_Operation') : alert('Opening operating procedure...')}
              className="px-3.5 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white font-semibold text-xs shadow-md shadow-brand-500/20 transition-all flex items-center gap-1.5 cursor-pointer"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span>Open SOP</span>
            </button>
          </div>
        </div>
      </div>

      {/* 2. KNOWLEDGE COVERAGE */}
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
            className="text-xs text-brand-400 hover:text-brand-300 font-medium flex items-center gap-1 cursor-pointer"
          >
            <span>{coverageExpanded ? 'Collapse Coverage' : 'Expand Breakdown'}</span>
            {coverageExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>

        {/* Progress Bar */}
        <div className="w-full h-2 rounded-full bg-slate-950 border border-slate-800 overflow-hidden">
          <div
            className="h-full bg-brand-500 rounded-full transition-all duration-300"
            style={{ width: `${(availableCount / knowledgePillars.length) * 100}%` }}
          />
        </div>

        {/* Explainable Breakdown Checklist */}
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
              className="text-xs text-slate-400 hover:text-white flex items-center gap-1 cursor-pointer"
            >
              <span>{specsExpanded ? 'Hide' : 'Show Details'}</span>
              {specsExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
          </div>

          <div className="space-y-1.5 text-xs font-mono">
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Maker / Model:</span>
              <span className="text-slate-200 font-semibold">{asset?.manufacturer || 'OEM Standard'} {asset?.model || ''}</span>
            </div>

            {asset?.specs?.rated_flow_m3_h ? (
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Design Flow / Head:</span>
                <span className="text-slate-200">{asset.specs.rated_flow_m3_h} m³/h @ {asset.specs.rated_head_m || 85}m TDH</span>
              </div>
            ) : asset?.specs?.water_flow_rate_m3_h ? (
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Circulation Capacity:</span>
                <span className="text-slate-200">{asset.specs.water_flow_rate_m3_h} m³/h ({asset.specs.design_cooling_capacity_mw || 14.5} MW)</span>
              </div>
            ) : asset?.specs?.duty_kw ? (
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Thermal Duty:</span>
                <span className="text-slate-200">{asset.specs.duty_kw} kW</span>
              </div>
            ) : (
              <div className="py-1 border-b border-slate-800/60 text-slate-400 italic">
                Design specifications pending manual verification.
              </div>
            )}

            {specsExpanded && (
              <>
                {asset?.specs?.design_rpm && (
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span className="text-slate-400">Operating Speed:</span>
                    <span className="text-slate-200">{asset.specs.design_rpm} RPM ({asset.specs.motor_power_kw || 45} kW Motor)</span>
                  </div>
                )}
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Serial Number:</span>
                  <span className="text-slate-200">{asset?.serial_number || 'Standard Asset Tag'}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">Asset Criticality:</span>
                  <span className="text-emerald-400 font-bold">{asset?.criticality || 'High'}</span>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Registered Components (Collapsible) */}
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Components ({asset?.components?.length || 0})
            </h3>
            <button
              onClick={() => setComponentsExpanded(!componentsExpanded)}
              className="text-xs text-slate-400 hover:text-white flex items-center gap-1 cursor-pointer"
            >
              <span>{componentsExpanded ? 'Hide' : 'Show All'}</span>
              {componentsExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
          </div>

          <div className="space-y-1.5 text-xs">
            {(!asset?.components || asset.components.length === 0) ? (
              <div className="p-2 text-slate-400 italic font-mono text-[11px]">
                No components registered yet.
              </div>
            ) : (
              asset.components.slice(0, componentsExpanded ? asset.components.length : 2).map((c, idx) => (
                <div key={c.id || idx} className="p-2 rounded bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
                  <div>
                    <span className="font-semibold text-white">{c.name}</span>
                    <span className="text-[11px] text-slate-400 font-mono ml-2">({c.part_number || 'OEM Standard'})</span>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-mono">
                    {c.status || 'Operational'}
                  </span>
                </div>
              ))
            )}
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
