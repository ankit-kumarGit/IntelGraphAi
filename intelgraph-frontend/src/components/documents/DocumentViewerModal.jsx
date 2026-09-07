import React, { useState, useEffect } from 'react';
import { X, FileText, CheckCircle2, AlertTriangle, Layers, Calendar, ExternalLink } from 'lucide-react';
import { api } from '../../services/api';

export default function DocumentViewerModal({ documentId, onClose }) {
  const [doc, setDoc] = useState(null);
  const [chunks, setChunks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('chunks'); // 'chunks' | 'metadata'

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      if (!documentId) return;
      setLoading(true);
      try {
        const [docData, chunksData] = await Promise.all([
          api.getDocument(documentId),
          api.getDocumentChunks(documentId)
        ]);
        if (isMounted) {
          setDoc(docData);
          setChunks(chunksData);
        }
      } catch (err) {
        console.error('Failed to load document details:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadData();
    return () => { isMounted = false; };
  }, [documentId]);

  if (!documentId) return null;

  return (
    <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-brand-500/10 text-brand-400 border border-brand-500/20">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <span>{doc?.title || documentId}</span>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                  {doc?.version || 'v1.0'}
                </span>
                <span className={`text-[10px] px-2 py-0.5 rounded uppercase font-semibold ${
                  doc?.governance_status === 'Approved'
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'bg-red-500/20 text-red-400 border border-red-500/30'
                }`}>
                  {doc?.governance_status || 'Draft'}
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Asset: {doc?.asset_tag} • Category: {doc?.category} • Uploaded: {doc?.upload_date}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {loading ? (
            <div className="py-16 text-center text-slate-400">
              <div className="w-7 h-7 border-2 border-brand-400 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
              Loading document chunks and verified sections...
            </div>
          ) : (
            <div className="space-y-4">
              {/* Document Summary */}
              {doc?.summary && (
                <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 text-xs text-slate-300">
                  <div className="font-semibold text-brand-400 mb-1 flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5" />
                    <span>Executive Document Summary</span>
                  </div>
                  <p className="leading-relaxed">{doc.summary}</p>
                </div>
              )}

              {/* Chunks List */}
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs font-semibold text-slate-400">
                  <span>Indexed Chunks ({chunks.length})</span>
                  <span className="font-mono text-[11px] text-slate-400">FAISS Searchable Units</span>
                </div>

                {chunks.map((chunk, idx) => (
                  <div
                    key={chunk.chunk_id || idx}
                    className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 space-y-2 text-xs"
                  >
                    <div className="flex items-center justify-between text-[11px] font-mono border-b border-slate-800/60 pb-2">
                      <span className="text-brand-400 font-semibold">
                        Page {chunk.page_number} • Section: {chunk.section_title}
                      </span>
                      <span className="text-slate-400">{chunk.chunk_id}</span>
                    </div>

                    <p className="text-slate-300 font-mono text-[11px] leading-relaxed whitespace-pre-wrap">
                      {chunk.content}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950 flex items-center justify-between text-xs text-slate-400">
          <span>Target File: {doc?.filename}</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-all"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
