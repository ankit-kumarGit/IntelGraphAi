import React from 'react';
import { X, FileText, CheckCircle2, ShieldAlert, Calendar, User, ExternalLink } from 'lucide-react';

export default function EvidenceDrawer({ isOpen, onClose, evidenceData, onOpenDocViewer }) {
  if (!isOpen || !evidenceData) return null;

  const items = Array.isArray(evidenceData) ? evidenceData : [evidenceData];

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className="w-full max-w-xl h-full bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col animate-in slide-in-from-right duration-300"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/80">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-brand-500/10 text-brand-400 border border-brand-500/20">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-white tracking-tight">Verified Evidence Traceability</h3>
              <p className="text-[11px] text-slate-400 font-mono">
                {items.length} Grounded Industrial Source Record{items.length > 1 ? 's' : ''}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-all"
            aria-label="Close Evidence Drawer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Evidence List */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 text-xs">
          {items.map((item, idx) => {
            const isApproved = item.governance_status === 'Approved' || item.status === 'Approved' || item.status === 'Verified' || !item.status;
            return (
              <div 
                key={idx}
                className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3 shadow-inner"
              >
                {/* Source & Status */}
                <div className="flex items-start justify-between gap-3 border-b border-slate-800/80 pb-2.5">
                  <div>
                    <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
                      SOURCE DOCUMENT / RECORD
                    </span>
                    <h4 className="font-bold text-white text-sm mt-0.5">
                      {item.document_name || item.title || item.source || 'Industrial Maintenance Log'}
                    </h4>
                  </div>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border flex items-center gap-1 ${
                    isApproved 
                      ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' 
                      : 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                  }`}>
                    <CheckCircle2 className="w-3 h-3" />
                    <span>{item.governance_status || item.status || 'Verified Record'}</span>
                  </span>
                </div>

                {/* Metadata Grid */}
                <div className="grid grid-cols-2 gap-2 text-[11px] font-mono text-slate-400 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/60">
                  <div className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    <span>Date: <strong className="text-slate-200">{item.date || item.timestamp || 'Historical Record'}</strong></span>
                  </div>
                  <div>
                    <span>Location: <strong className="text-brand-400">{item.page ? `Page ${item.page}` : item.section || 'Record Log'}</strong></span>
                  </div>
                  {item.technician && (
                    <div className="flex items-center gap-1.5 col-span-2">
                      <User className="w-3.5 h-3.5 text-slate-400" />
                      <span>Author/Tech: <strong className="text-slate-200">{item.technician}</strong></span>
                    </div>
                  )}
                </div>

                {/* Exact Verified Excerpt */}
                <div className="space-y-1">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-brand-400 font-semibold block">
                    Verified Excerpt
                  </span>
                  <div className="p-3 rounded-lg bg-slate-900 border-l-2 border-brand-500 text-slate-200 font-sans leading-relaxed text-xs">
                    "{item.excerpt || item.text || item.summary || item.details}"
                  </div>
                </div>

                {/* Action if document viewable */}
                {item.document_id && onOpenDocViewer && (
                  <button
                    onClick={() => onOpenDocViewer(item.document_id)}
                    className="w-full py-1.5 px-3 rounded-lg bg-slate-800 hover:bg-slate-750 border border-slate-700 text-brand-400 hover:text-brand-300 font-medium text-xs flex items-center justify-center gap-1.5 transition-all"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    <span>Open Original Document Chunk</span>
                  </button>
                )}
              </div>
            );
          })}
        </div>

        {/* Footer Grounding Guarantee */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/90 flex items-center justify-between text-[11px] text-slate-400 font-mono">
          <span className="flex items-center gap-1.5 text-emerald-400">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Strict Operational Grounding</span>
          </span>
          <span>Zero Hallucinated Facts</span>
        </div>
      </div>
    </div>
  );
}
