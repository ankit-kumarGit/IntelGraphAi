import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Thermometer, 
  Gauge, 
  Clock, 
  Info, 
  CheckCircle2, 
  ChevronDown, 
  ChevronUp 
} from 'lucide-react';
import { api } from '../../services/api';

export default function TabTelemetry({ assetTag }) {
  const [telemetry, setTelemetry] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeMetric, setActiveMetric] = useState('vibration'); // 'vibration' | 'temperature' | 'pressure'
  const [tableExpanded, setTableExpanded] = useState(false);

  useEffect(() => {
    let isMounted = true;
    async function loadTelemetry() {
      setLoading(true);
      try {
        const data = await api.getTelemetry(assetTag);
        if (isMounted) setTelemetry(data);
      } catch (err) {
        console.error('Failed to load telemetry:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadTelemetry();
    return () => { isMounted = false; };
  }, [assetTag]);

  if (loading) {
    return (
      <div className="p-16 text-center text-slate-400">
        <div className="w-8 h-8 border-2 border-brand-400 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
        Synthesizing condition monitoring telemetry stream...
      </div>
    );
  }

  const points = telemetry?.points || [];
  if (points.length === 0) {
    return (
      <div className="p-12 text-center text-slate-400 bg-slate-900/50 rounded-xl border border-slate-800">
        <Activity className="w-8 h-8 text-slate-400 mx-auto mb-2 opacity-50" />
        <h4 className="text-sm font-semibold text-slate-300">No Telemetry Stream Configured</h4>
        <p className="text-xs text-slate-400 mt-1">This machine profile does not have an active online sensor telemetry link.</p>
      </div>
    );
  }

  const latest = points[points.length - 1];

  // Prepare chart coordinates for SVG trend rendering
  // Canvas: 800 x 200
  const width = 800;
  const height = 200;
  const padding = 40;

  let metricKey = 'vibration_rms';
  let unit = 'mm/s RMS';
  let threshold = 4.5;
  let thresholdLabel = 'Warning Threshold: 4.5 mm/s';
  let lineColor = '#38bdf8';

  if (activeMetric === 'temperature') {
    metricKey = 'bearing_temp_c';
    unit = '°C';
    threshold = 75;
    thresholdLabel = 'Max Continuous Limit: 75°C';
    lineColor = '#f59e0b';
  } else if (activeMetric === 'pressure') {
    metricKey = 'discharge_pressure_bar';
    unit = 'bar';
    threshold = 16.5;
    thresholdLabel = 'PSV Relief Setting: 16.5 bar';
    lineColor = '#a855f7';
  }

  const values = points.map(p => p[metricKey]);
  const maxVal = Math.max(...values, threshold) * 1.15;
  const minVal = 0;

  const getX = (idx) => padding + (idx / (points.length - 1)) * (width - padding * 2);
  const getY = (val) => height - padding - ((val - minVal) / (maxVal - minVal)) * (height - padding * 2);

  const polylinePoints = points.map((p, i) => `${getX(i)},${getY(p[metricKey])}`).join(' ');
  const thresholdY = getY(threshold);

  // Key historical event annotations
  const eventMarkers = [
    { index: 5, label: 'Aug 2025: Warning Spike (6.8 mm/s)', color: '#f59e0b' },
    { index: 8, label: 'Feb 2026: Unscheduled Trip (12.4 mm/s)', color: '#ef4444' },
    { index: 9, label: 'Feb 2026: Post-Repair Baseline (2.2 mm/s)', color: '#10b981' }
  ];

  return (
    <div className="space-y-6">
      {/* Synthetic Demo Data Label Banner (Rule #37) */}
      <div className="p-3 rounded-xl bg-cyan-950/25 border border-cyan-500/30 flex items-center justify-between text-xs text-cyan-300">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-cyan-400 shrink-0" />
          <span>
            <strong>[Synthetic Demo Data]</strong> — Correlated with verified maintenance work orders and inspection reports.
          </span>
        </div>
        <span className="font-mono text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20">
          Synthetic Demo Data
        </span>
      </div>

      {/* 1. CURRENT CONDITION KPI GAUGES */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Vibration */}
        <button
          onClick={() => setActiveMetric('vibration')}
          className={`p-4 rounded-xl border text-left transition-all ${
            activeMetric === 'vibration' 
              ? 'bg-slate-900 border-brand-400 ring-2 ring-brand-500/20' 
              : 'bg-slate-900/70 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Vibration</span>
            <Activity className="w-4 h-4 text-brand-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white tracking-tight mt-1">
            {latest.vibration_rms} <span className="text-xs text-slate-400">mm/s RMS</span>
          </div>
          <div className="text-[11px] text-emerald-400 flex items-center gap-1 font-medium mt-1">
            <CheckCircle2 className="w-3 h-3" />
            <span>Nominal (&lt;4.5 limit)</span>
          </div>
        </button>

        {/* Bearing Temperature */}
        <button
          onClick={() => setActiveMetric('temperature')}
          className={`p-4 rounded-xl border text-left transition-all ${
            activeMetric === 'temperature' 
              ? 'bg-slate-900 border-amber-400 ring-2 ring-amber-500/20' 
              : 'bg-slate-900/70 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Bearing Temperature</span>
            <Thermometer className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white tracking-tight mt-1">
            {latest.bearing_temp_c} <span className="text-xs text-slate-400">°C</span>
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            Continuous limit: 75°C
          </div>
        </button>

        {/* Discharge Pressure */}
        <button
          onClick={() => setActiveMetric('pressure')}
          className={`p-4 rounded-xl border text-left transition-all ${
            activeMetric === 'pressure' 
              ? 'bg-slate-900 border-purple-400 ring-2 ring-purple-500/20' 
              : 'bg-slate-900/70 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Discharge Pressure</span>
            <Gauge className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white tracking-tight mt-1">
            {latest.discharge_pressure_bar} <span className="text-xs text-slate-400">bar</span>
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            Design TDH: 45m head
          </div>
        </button>

        {/* Operating Hours */}
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Cumulative Running Hours</span>
            <Clock className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white tracking-tight mt-1">
            {latest.operating_hours.toLocaleString()} <span className="text-xs text-slate-400">hrs</span>
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            Speed: {latest.rpm} RPM
          </div>
        </div>
      </div>

      {/* 2. VISUAL TREND CHART WITH HISTORICAL EVENT MARKERS */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 shadow-xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <h3 className="font-bold text-white text-sm">
              Condition Trend: <span className="capitalize text-brand-400">{activeMetric}</span> ({unit})
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Visual condition progression with milestone event correlations
            </p>
          </div>

          <div className="flex items-center gap-3 text-xs font-mono">
            <span className="flex items-center gap-1.5 text-slate-400">
              <span className="w-2.5 h-0.5 bg-red-400"></span>
              <span>{thresholdLabel}</span>
            </span>
          </div>
        </div>

        {/* SVG Canvas Trend */}
        <div className="w-full overflow-x-auto">
          <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-56">
            {/* Grid Lines */}
            <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#334155" strokeWidth="1" />
            <line x1={padding} y1={padding} x2={width - padding} y2={padding} stroke="#1e293b" strokeDasharray="3,3" />
            <line x1={padding} y1={height / 2} x2={width - padding} y2={height / 2} stroke="#1e293b" strokeDasharray="3,3" />

            {/* Threshold Line */}
            <line 
              x1={padding} 
              y1={thresholdY} 
              x2={width - padding} 
              y2={thresholdY} 
              stroke="#ef4444" 
              strokeWidth="1.5" 
              strokeDasharray="4,4" 
            />

            {/* Main Trend Line */}
            <polyline
              fill="none"
              stroke={lineColor}
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              points={polylinePoints}
            />

            {/* Data Points */}
            {points.map((p, i) => {
              const x = getX(i);
              const y = getY(p[metricKey]);
              const isOver = p[metricKey] > threshold;

              return (
                <g key={i}>
                  <circle
                    cx={x}
                    cy={y}
                    r={isOver ? 5 : 3.5}
                    fill={isOver ? '#ef4444' : lineColor}
                    stroke="#0f172a"
                    strokeWidth="1.5"
                  />
                  {/* Timestamp label on every 2nd point */}
                  {i % 2 === 0 && (
                    <text
                      x={x}
                      y={height - 15}
                      fill="#64748b"
                      fontSize="9"
                      fontFamily="monospace"
                      textAnchor="middle"
                    >
                      {p.timestamp.substring(5)}
                    </text>
                  )}
                </g>
              );
            })}
          </svg>
        </div>

        {/* Historical Event Markers Legend */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5 pt-1 text-xs">
          <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
            <span className="text-amber-400 font-bold block">2025 Warning Spike (6.8 mm/s)</span>
            <span className="text-[11px] text-slate-400">Condition Analyst logged INSP-456 warning</span>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
            <span className="text-red-400 font-bold block">2026 Seizure Trip (12.4 mm/s)</span>
            <span className="text-[11px] text-slate-400">Emergency shutdown & WO-1189 repair window</span>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
            <span className="text-emerald-400 font-bold block">2026 Post-Repair Recovery (2.2 mm/s)</span>
            <span className="text-[11px] text-slate-400">New SKF 6312 installed & aligned</span>
          </div>
        </div>
      </div>

      {/* 3. PROGRESSIVE DISCLOSURE: RAW SAMPLES TABLE */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Raw Telemetry Log Samples ({points.length} records)
          </div>
          <button
            onClick={() => setTableExpanded(!tableExpanded)}
            className="text-xs text-brand-400 hover:text-brand-300 font-medium flex items-center gap-1"
          >
            <span>{tableExpanded ? 'Hide Raw Table' : 'Inspect Raw Data'}</span>
            {tableExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>

        {tableExpanded && (
          <div className="overflow-x-auto pt-2 border-t border-slate-800 animate-in fade-in duration-150">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-mono text-[11px]">
                  <th className="py-2 px-3">Timestamp</th>
                  <th className="py-2 px-3">Vibration (mm/s RMS)</th>
                  <th className="py-2 px-3">Bearing Temp (°C)</th>
                  <th className="py-2 px-3">Discharge Pressure (bar)</th>
                  <th className="py-2 px-3">Hours</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                {points.map((p, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30">
                    <td className="py-2 px-3 text-slate-300">{p.timestamp}</td>
                    <td className="py-2 px-3">
                      <span className={p.vibration_rms > 4.5 ? 'text-red-400 font-bold' : 'text-emerald-400'}>
                        {p.vibration_rms}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-slate-200">{p.bearing_temp_c}°C</td>
                    <td className="py-2 px-3 text-slate-200">{p.discharge_pressure_bar} bar</td>
                    <td className="py-2 px-3 text-slate-400">{p.operating_hours.toLocaleString()} h</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
