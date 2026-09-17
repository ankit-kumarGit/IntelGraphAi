import React, { useState, useEffect } from 'react';
import { 
  Network, 
  FileText, 
  FileCode, 
  CheckCircle2, 
  AlertTriangle, 
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Search,
  Play,
  RotateCw,
  Sparkles,
  UserCheck,
  Check
} from 'lucide-react';
import { api } from '../../services/api';
import GraphCanvas from './GraphCanvas';
import DocumentViewerModal from '../documents/DocumentViewerModal';

export default function KnowledgeView({ onSelectAsset }) {
  const [selectedAssetTag, setSelectedAssetTag] = useState('P-101');
  const [mapData, setMapData] = useState({ nodes: [], links: [] });
  const [graphLoading, setGraphLoading] = useState(true);

  // Quarantined OCR / Tag Review Queue State
  const [quarantinedItems, setQuarantinedItems] = useState([
    {
      id: 'q-tag-01',
      raw_tag: 'P10I',
      drawing_source: 'Unit2_Visual_Engineering_PID.png',
      spatial_grid: 'Grid-B / Zone-1',
      engine: 'Tesseract 5.5.3',
      confidence_pct: 40.0,
      classification: 'Centrifugal Pump',
      suggested_canonical: 'P-101',
      status: 'Quarantined (Safety Guardrail: Conf < 85%)',
      reason: 'Degraded pixel contrast / optical OCR ambiguity between character "I" and digit "1". Auto-linking blocked to prevent hallucination.'
    }
  ]);
  const [confirmingId, setConfirmingId] = useState(null);
  const [reviewMessage, setReviewMessage] = useState(null);

  // Documents State
  const [documents, setDocuments] = useState([]);
  const [docFilter, setDocFilter] = useState('all');
  const [docSearch, setDocSearch] = useState('');
  const [selectedDocId, setSelectedDocId] = useState(null);

  // Collapsible Secondary Sections
  const [pidExpanded, setPidExpanded] = useState(false);
  const [pidText, setPidText] = useState(
    "Line 101-A: Feed Suction -> P-101 (Primary Pump) -> V-102 (Discharge Control Valve)\n" +
    "Line 101-B: Pressure Transmitter PT-101 -> Suction Strainer STR-101\n" +
    "Safety Loop: Pressure Safety Valve PSV-101 set at 16.5 bar"
  );
  const [pidTags, setPidTags] = useState([]);
  const [extractingPid, setExtractingPid] = useState(false);

  // Load Graph Data for Selected Asset
  useEffect(() => {
    let isMounted = true;
    async function loadGraph() {
      setGraphLoading(true);
      try {
        const [graphRes, docsRes] = await Promise.all([
          api.getKnowledgeMap(selectedAssetTag),
          api.getDocuments()
        ]);
        if (isMounted) {
          setMapData(graphRes);
          setDocuments(docsRes);
        }
      } catch (err) {
        console.error('Failed to load knowledge data:', err);
      } finally {
        if (isMounted) setGraphLoading(false);
      }
    }
    loadGraph();
    return () => { isMounted = false; };
  }, [selectedAssetTag]);

  const handleRunPIDExtraction = async () => {
    setExtractingPid(true);
    try {
      const res = await api.extractPIDTags(pidText, 'Unit 2 Process Flowsheet');
      setPidTags(res.tags || []);
    } catch (err) {
      alert('P&ID extraction failed: ' + err.message);
    } finally {
      setExtractingPid(false);
    }
  };

  const handleConfirmQuarantined = async (item) => {
    setConfirmingId(item.id);
    try {
      const formData = new FormData();
      formData.append('document_id', 'Unit2_Visual_Engineering_PID');
      formData.append('confirmed_asset_tag', item.suggested_canonical);
      formData.append('event_type', 'P&ID Verified Extraction');
      formData.append('event_date', '2026-09-12');
      formData.append('component', item.classification);
      formData.append('work_order', 'ENG-PID-U2');
      formData.append('confirmed_by', 'Lead Reliability Analyst');

      await api.confirmExtraction(formData);
      setQuarantinedItems(prev => prev.map(q => 
        q.id === item.id 
          ? { ...q, status: 'Confirmed & Linked to P-101', confirmed: true } 
          : q
      ));
      setReviewMessage(`Tag '${item.raw_tag}' verified as canonical '${item.suggested_canonical}' and committed to Knowledge Graph.`);
      setTimeout(() => setReviewMessage(null), 5000);
    } catch (err) {
      alert('Confirmation failed: ' + err.message);
    } finally {
      setConfirmingId(null);
    }
  };

  const handleRejectQuarantined = (itemId) => {
    setQuarantinedItems(prev => prev.filter(q => q.id !== itemId));
    setReviewMessage('Quarantined extraction rejected and discarded from graph queue.');
    setTimeout(() => setReviewMessage(null), 4000);
  };

  // Filtered documents
  const filteredDocs = documents.filter((d) => {
    const matchesFilter = docFilter === 'all' || d.governance_status?.toLowerCase() === docFilter.toLowerCase();
    const matchesSearch = !docSearch || d.title?.toLowerCase().includes(docSearch.toLowerCase()) || d.filename?.toLowerCase().includes(docSearch.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const approvedCount = documents.filter(d => d.governance_status === 'Approved').length;
  const obsoleteCount = documents.filter(d => d.governance_status === 'Obsolete').length;
  const reviewCount = documents.filter(d => d.governance_status === 'Under Review' || d.governance_status === 'Draft').length;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* 1. KNOWLEDGE BRAIN HEADER */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="text-xs font-mono tracking-wider uppercase text-slate-400 font-semibold mb-1">
            Unified Knowledge Graph
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Network className="w-6 h-6 text-brand-400" />
            <span>Industrial Knowledge Brain</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Explore directional relationships between machinery, components, manuals, maintenance, and failure modes
          </p>
        </div>

        {/* Machine Focus Switcher */}
        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-400 font-medium">Focus Machine:</span>
          <select
            value={selectedAssetTag}
            onChange={(e) => setSelectedAssetTag(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-brand-400 font-mono font-bold text-xs focus:outline-none focus:border-brand-500"
          >
            <option value="P-101">P-101 (Centrifugal Water Pump)</option>
            <option value="P-102">P-102 (Booster Standby Pump)</option>
            <option value="C-201">C-201 (Reciprocating Compressor)</option>
            <option value="P-205">P-205 (Slurry Transfer Pump)</option>
          </select>
        </div>
      </div>

      {/* 2. PRIMARY VISUAL ELEMENT: REAL INTERACTIVE KNOWLEDGE GRAPH (Section 11, 12, 13) */}
      <section className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span className="font-bold text-white uppercase tracking-wider text-xs">
              Knowledge Graph Canvas
            </span>
            <span className="text-slate-400 font-mono">
              (Interactive Directed Network)
            </span>
          </div>
          <span className="text-slate-400 font-mono text-[11px]">
            Double-click or drag canvas to pan • Scroll to zoom
          </span>
        </div>

        {graphLoading ? (
          <div className="h-[560px] rounded-2xl bg-slate-950 border border-slate-800 flex items-center justify-center text-slate-400">
            <div className="text-center space-y-2">
              <div className="w-8 h-8 border-2 border-brand-400 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p className="text-xs">Generating neural knowledge relationships for {selectedAssetTag}...</p>
            </div>
          </div>
        ) : (
          <GraphCanvas
            rawNodes={mapData.nodes}
            rawLinks={mapData.links}
            assetTag={selectedAssetTag}
            onOpenDocViewer={(id) => setSelectedDocId(id)}
          />
        )}
      </section>

      {/* 3. DOCUMENT LIFECYCLE PROGRESSION (Section 18) */}
      <section className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2 text-xs">
        <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block">
          Knowledge Ingestion & Governance Pipeline
        </span>
        <div className="flex flex-wrap items-center justify-between gap-2 pt-1 font-mono text-[11px]">
          {[
            { step: '1. Uploaded', desc: 'Raw PDF / Drawing', active: true },
            { step: '2. Processing', desc: 'OCR & Parsing', active: true },
            { step: '3. Extracted', desc: 'Entities & Limits', active: true },
            { step: '4. Needs Review', desc: 'Engineer Verification', active: true },
            { step: '5. Confirmed', desc: 'Governed Status', active: true },
            { step: '6. Available to AI', desc: 'Strict Grounding', active: true },
          ].map((s, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <div className="flex items-center gap-1 text-emerald-400 font-medium">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>{s.step}</span>
              </div>
              {idx < 5 && <span className="text-slate-600 hidden sm:inline">→</span>}
            </div>
          ))}
        </div>
      </section>

      {/* 4. SECONDARY CONTENT: KNOWLEDGE SOURCES (Section 16 & 17) */}
      <section className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div>
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
              Knowledge Sources
            </h2>
            <div className="text-xs text-slate-400 mt-0.5 flex items-center gap-2 font-mono">
              <span>{documents.length} Documents</span>
              <span>•</span>
              <span className="text-emerald-400 font-semibold">{approvedCount} Approved</span>
              <span>•</span>
              <span className="text-red-400 font-semibold">{obsoleteCount} Obsolete</span>
              <span>•</span>
              <span className="text-amber-400 font-semibold">{reviewCount} Under Review</span>
            </div>
          </div>

          {/* Search & Filter */}
          <div className="flex items-center gap-2 text-xs">
            <div className="relative w-44">
              <Search className="w-3 h-3 absolute left-2.5 top-2 text-slate-400" />
              <input
                type="text"
                value={docSearch}
                onChange={(e) => setDocSearch(e.target.value)}
                placeholder="Search documents..."
                className="w-full pl-7 pr-2 py-1 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white placeholder-slate-400 focus:outline-none"
              />
            </div>

            <div className="flex items-center gap-1">
              {['all', 'Approved', 'Obsolete'].map((f) => (
                <button
                  key={f}
                  onClick={() => setDocFilter(f)}
                  className={`px-2.5 py-1 rounded capitalize font-medium text-[11px] transition-all ${
                    docFilter === f ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Compact Document List (Essential Columns Only: Document, Type, Version, Status, Review Date, Action) */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/80 text-slate-400 font-mono text-[11px]">
                <th className="py-2.5 px-4">Document Title</th>
                <th className="py-2.5 px-4">Type</th>
                <th className="py-2.5 px-4">Version</th>
                <th className="py-2.5 px-4">Status</th>
                <th className="py-2.5 px-4">Review Date</th>
                <th className="py-2.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
              {filteredDocs.map((doc) => {
                const isApproved = doc.governance_status === 'Approved';
                const isObsolete = doc.governance_status === 'Obsolete';

                return (
                  <tr 
                    key={doc.document_id} 
                    className={`hover:bg-slate-800/30 transition-colors ${isObsolete ? 'opacity-40' : ''}`}
                  >
                    <td className="py-2.5 px-4 font-sans font-medium text-white">
                      <div className="truncate max-w-xs">{doc.title || doc.filename}</div>
                    </td>
                    <td className="py-2.5 px-4 text-slate-400">{doc.category}</td>
                    <td className="py-2.5 px-4 text-slate-300">{doc.version}</td>
                    <td className="py-2.5 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                        isApproved ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' : 'bg-red-500/15 text-red-400 border border-red-500/30'
                      }`}>
                        {doc.governance_status}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-slate-400">
                      {doc.upload_date || '2026-03-01'}
                    </td>
                    <td className="py-2.5 px-4 text-right">
                      <button
                        onClick={() => setSelectedDocId(doc.document_id)}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-brand-400 hover:text-brand-300 font-medium text-xs transition-all"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* 5. SECONDARY ENGINEERING TOOL: P&ID TAG EXTRACTOR (Collapsible) */}
      <section className="rounded-xl border border-slate-800 bg-slate-900 p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileCode className="w-4 h-4 text-cyan-400" />
            <span className="font-bold text-xs uppercase tracking-wider text-slate-200">
              P&ID Equipment Tag Linking Tool
            </span>
          </div>
          <button
            onClick={() => setPidExpanded(!pidExpanded)}
            className="text-xs text-slate-400 hover:text-white flex items-center gap-1"
          >
            <span>{pidExpanded ? 'Hide' : 'Open P&ID Extractor'}</span>
            {pidExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>

        {pidExpanded && (
          <div className="pt-3 border-t border-slate-800 space-y-3 text-xs animate-in fade-in duration-150">
            <textarea
              rows={4}
              value={pidText}
              onChange={(e) => setPidText(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 font-mono focus:outline-none focus:border-brand-500"
            />
            <div className="flex justify-end">
              <button
                onClick={handleRunPIDExtraction}
                disabled={extractingPid}
                className="px-4 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white font-semibold text-xs transition-all flex items-center gap-1.5 disabled:opacity-50"
              >
                {extractingPid ? <RotateCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                <span>Extract P&ID Equipment Tags</span>
              </button>
            </div>

            {/* 7-STAGE PIPELINE TRANSPARENCY MATRIX */}
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-300">
                  P&ID Computer Vision Capability & Limitation Matrix (7-Stage Pipeline)
                </span>
                <span className="text-[10px] font-mono text-slate-500">5 Available • 2 Limitations</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 text-[11px]">
                <div className="p-2 rounded bg-slate-900 border border-emerald-500/30">
                  <div className="flex items-center justify-between text-emerald-400 font-semibold mb-0.5">
                    <span>1. Pixel OCR</span>
                    <span className="text-[9px] px-1.5 py-0.2 rounded bg-emerald-500/20">AVAILABLE</span>
                  </div>
                  <p className="text-[10px] text-slate-400">Tesseract v5.5.0 on image pixels</p>
                </div>
                <div className="p-2 rounded bg-slate-900 border border-emerald-500/30">
                  <div className="flex items-center justify-between text-emerald-400 font-semibold mb-0.5">
                    <span>2. Tag Detection</span>
                    <span className="text-[9px] px-1.5 py-0.2 rounded bg-emerald-500/20">AVAILABLE</span>
                  </div>
                  <p className="text-[10px] text-slate-400">ISA-5.1 regex pattern matching</p>
                </div>
                <div className="p-2 rounded bg-slate-900 border border-emerald-500/30">
                  <div className="flex items-center justify-between text-emerald-400 font-semibold mb-0.5">
                    <span>3. Bounding Boxes</span>
                    <span className="text-[9px] px-1.5 py-0.2 rounded bg-emerald-500/20">AVAILABLE</span>
                  </div>
                  <p className="text-[10px] text-slate-400">Exact pixel coordinates (x, y, w, h)</p>
                </div>
                <div className="p-2 rounded bg-slate-900 border border-emerald-500/30">
                  <div className="flex items-center justify-between text-emerald-400 font-semibold mb-0.5">
                    <span>4. Classification</span>
                    <span className="text-[9px] px-1.5 py-0.2 rounded bg-emerald-500/20">AVAILABLE</span>
                  </div>
                  <p className="text-[10px] text-slate-400">Pumps, Compressors, Transmitters</p>
                </div>
                <div className="p-2 rounded bg-slate-900 border border-emerald-500/30">
                  <div className="flex items-center justify-between text-emerald-400 font-semibold mb-0.5">
                    <span>5. Spatial Grid</span>
                    <span className="text-[9px] px-1.5 py-0.2 rounded bg-emerald-500/20">AVAILABLE</span>
                  </div>
                  <p className="text-[10px] text-slate-400">Grid zones & Neo4j graph linking</p>
                </div>
                <div className="p-2 rounded bg-slate-900 border border-amber-500/30">
                  <div className="flex items-center justify-between text-amber-400 font-semibold mb-0.5">
                    <span>6. Symbol Detect</span>
                    <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-500/20">LIMITATION</span>
                  </div>
                  <p className="text-[10px] text-slate-400">No deep-learning YOLO icon model</p>
                </div>
                <div className="p-2 rounded bg-slate-900 border border-amber-500/30 col-span-1 sm:col-span-2">
                  <div className="flex items-center justify-between text-amber-400 font-semibold mb-0.5">
                    <span>7. Pipe Topology Inference</span>
                    <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-500/20">LIMITATION</span>
                  </div>
                  <p className="text-[10px] text-slate-400">Contour line tracing not implemented; topology infers from ontology</p>
                </div>
              </div>
            </div>

            {pidTags.length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2">
                {pidTags.map((t, idx) => (
                  <div key={idx} className="p-2.5 rounded bg-slate-950 border border-slate-800 text-xs space-y-1">
                    <div className="flex justify-between font-mono">
                      <span className="font-bold text-brand-400">{t.tag}</span>
                      <span className="text-[10px] text-slate-400">{t.type}</span>
                    </div>
                    <p className="text-[11px] text-slate-400 truncate">{t.context_snippet}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </section>

      {/* 6. QUARANTINED OCR & HUMAN-IN-THE-LOOP REVIEW QUEUE */}
      <section className="rounded-xl border border-amber-500/30 bg-slate-900 p-5 space-y-4 shadow-lg shadow-black/20">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <UserCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-white flex items-center gap-2">
                <span>Quarantined OCR & Human-in-the-Loop Review Queue</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-amber-500/20 text-amber-400 border border-amber-500/30">
                  {quarantinedItems.filter(q => !q.confirmed).length} Pending
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Low-confidence optical detections (&lt;85%) quarantined by safety guardrails to prevent ungrounded graph pollution
              </p>
            </div>
          </div>
          {reviewMessage && (
            <div className="px-3 py-1.5 rounded-lg bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 text-xs flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>{reviewMessage}</span>
            </div>
          )}
        </div>

        <div className="space-y-3">
          {quarantinedItems.map((item) => (
            <div 
              key={item.id}
              className={`p-4 rounded-xl border text-xs transition-all ${
                item.confirmed 
                  ? 'bg-emerald-950/20 border-emerald-500/30 opacity-90'
                  : 'bg-slate-950/80 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 border-b border-slate-800/80">
                <div className="flex items-center gap-3">
                  <span className="px-2.5 py-1 rounded bg-amber-500/15 text-amber-400 border border-amber-500/30 font-mono font-bold text-xs">
                    OCR: {item.raw_tag}
                  </span>
                  <span className="text-slate-400">→</span>
                  <span className="text-brand-400 font-mono font-bold text-xs bg-brand-500/10 px-2 py-0.5 rounded border border-brand-500/20">
                    Candidate: {item.suggested_canonical}
                  </span>
                  <span className="text-slate-400 hidden sm:inline">•</span>
                  <span className="text-slate-300 hidden sm:inline">{item.classification}</span>
                </div>

                <div className="flex items-center gap-2 font-mono text-[11px]">
                  <span className="text-slate-400">Confidence:</span>
                  <span className={`font-bold ${item.confidence_pct >= 85 ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {item.confidence_pct.toFixed(1)}%
                  </span>
                  <span className="text-slate-600">|</span>
                  <span className="text-slate-400">{item.spatial_grid}</span>
                </div>
              </div>

              <div className="py-2.5 text-slate-300 leading-relaxed text-[11px] space-y-1">
                <p><strong className="text-slate-400">Source:</strong> {item.drawing_source} (Engine: {item.engine})</p>
                <p><strong className="text-slate-400">Safety Guardrail Reason:</strong> {item.reason}</p>
              </div>

              <div className="pt-2 flex items-center justify-between">
                <span className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                  item.confirmed ? 'text-emerald-400 bg-emerald-500/10' : 'text-amber-400 bg-amber-500/10'
                }`}>
                  Status: {item.status}
                </span>

                {!item.confirmed ? (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleRejectQuarantined(item.id)}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-xs transition-all"
                    >
                      Reject & Discard
                    </button>
                    <button
                      onClick={() => handleConfirmQuarantined(item)}
                      disabled={confirmingId === item.id}
                      className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition-all flex items-center gap-1.5 shadow-md shadow-emerald-600/20 disabled:opacity-50"
                    >
                      {confirmingId === item.id ? <RotateCw className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                      <span>Approve & Link to P-101</span>
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-1.5 text-emerald-400 text-xs font-semibold">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Committed to Knowledge Graph</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Document Viewer Modal */}
      {selectedDocId && (
        <DocumentViewerModal
          documentId={selectedDocId}
          onClose={() => setSelectedDocId(null)}
        />
      )}
    </div>
  );
}
