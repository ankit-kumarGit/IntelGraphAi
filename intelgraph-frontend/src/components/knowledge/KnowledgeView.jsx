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
  ArrowRight
} from 'lucide-react';
import { api } from '../../services/api';
import GraphCanvas from './GraphCanvas';
import DocumentViewerModal from '../documents/DocumentViewerModal';

export default function KnowledgeView({ onSelectAsset }) {
  const [selectedAssetTag, setSelectedAssetTag] = useState('P-101');
  const [mapData, setMapData] = useState({ nodes: [], links: [] });
  const [graphLoading, setGraphLoading] = useState(true);

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
