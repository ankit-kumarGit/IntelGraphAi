import React, { useState, useEffect } from 'react';
import { Search, X, Cpu, FileText, Wrench, AlertTriangle, ArrowRight, Sparkles } from 'lucide-react';
import { api } from '../../services/api';

export default function GlobalSearchModal({ isOpen, onClose, onSelectAsset, onOpenDocViewer }) {
  const [query, setQuery] = useState('');
  const [resolvedTag, setResolvedTag] = useState(null);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setResolvedTag(null);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        // 1. Entity resolution
        const resolved = await api.resolveTag(query);
        setResolvedTag(resolved);

        // 2. Search documents & assets
        const docs = await api.getDocuments();
        const assets = await api.getAssets();

        const qLower = query.toLowerCase();
        const matches = [];

        // Match assets
        for (const a of assets) {
          if (a.tag.toLowerCase().includes(qLower) || a.name.toLowerCase().includes(qLower)) {
            matches.push({ type: 'asset', id: a.tag, title: `${a.tag} - ${a.name}`, subtitle: `${a.plant} • Status: ${a.status}` });
          }
          // Components
          for (const c of a.components || []) {
            if (c.name.toLowerCase().includes(qLower)) {
              matches.push({ type: 'component', id: a.tag, title: `${c.name} (${a.tag})`, subtitle: `Part: ${c.part_number || 'OEM'} • Status: ${c.status}` });
            }
          }
        }

        // Match docs
        for (const d of docs) {
          if (d.title.toLowerCase().includes(qLower) || d.category.toLowerCase().includes(qLower) || d.filename.toLowerCase().includes(qLower)) {
            matches.push({ type: 'document', id: d.document_id, title: d.title || d.filename, subtitle: `Asset: ${d.asset_tag} • ${d.category} (${d.version})` });
          }
        }

        setResults(matches.slice(0, 10));
      } catch (err) {
        console.error('Search error:', err);
      } finally {
        setLoading(false);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [query]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-start justify-center pt-20 p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Input Bar */}
        <div className="p-4 border-b border-slate-800 flex items-center gap-3 bg-slate-950">
          <Search className="w-5 h-5 text-brand-400 shrink-0" />
          <input
            type="text"
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search equipment tags (e.g. Pump 101, P-101), documents, components, work orders..."
            className="flex-1 bg-transparent border-none text-white text-sm placeholder-slate-400 focus:outline-none"
          />
          <button
            onClick={onClose}
            className="p-1 rounded bg-slate-800 text-slate-400 hover:text-white text-xs font-mono"
          >
            ESC
          </button>
        </div>

        {/* Entity Resolution Suggestion */}
        {resolvedTag && resolvedTag.match_type !== 'unmatched' && (
          <div className="px-4 py-2 bg-brand-950/30 border-b border-brand-500/20 text-xs flex items-center justify-between text-brand-300">
            <div className="flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5 text-brand-400" />
              <span>
                Entity Resolution: <strong>{query}</strong> resolves to canonical machine tag{' '}
                <strong className="text-white font-mono bg-brand-500/20 px-1.5 py-0.5 rounded">{resolvedTag.canonical_tag}</strong>
              </span>
            </div>
            <button
              onClick={() => {
                onSelectAsset(resolvedTag.canonical_tag);
                onClose();
              }}
              className="font-bold underline hover:text-white"
            >
              Open Profile →
            </button>
          </div>
        )}

        {/* Results List */}
        <div className="max-h-96 overflow-y-auto p-3 space-y-1 text-xs">
          {loading ? (
            <div className="py-8 text-center text-slate-400">
              Searching hybrid knowledge index...
            </div>
          ) : results.length === 0 ? (
            <div className="py-8 text-center text-slate-400">
              {query ? 'No matching equipment or records found.' : 'Type a query or industrial tag to begin searching.'}
            </div>
          ) : (
            results.map((item, idx) => (
              <button
                key={idx}
                onClick={() => {
                  if (item.type === 'asset' || item.type === 'component') {
                    onSelectAsset(item.id);
                  } else if (item.type === 'document') {
                    onOpenDocViewer(item.id);
                  }
                  onClose();
                }}
                className="w-full text-left p-3 rounded-xl hover:bg-slate-850 border border-transparent hover:border-slate-800 flex items-center justify-between transition-all group"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-slate-800 text-slate-300 group-hover:text-brand-400">
                    {item.type === 'asset' ? <Cpu className="w-4 h-4" /> : item.type === 'component' ? <Wrench className="w-4 h-4" /> : <FileText className="w-4 h-4" />}
                  </div>
                  <div>
                    <div className="font-semibold text-white group-hover:text-brand-300">
                      {item.title}
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono">
                      {item.subtitle}
                    </div>
                  </div>
                </div>

                <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-brand-400 transition-transform group-hover:translate-x-1" />
              </button>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-slate-800 bg-slate-950 flex items-center justify-between text-[11px] text-slate-400 font-mono">
          <span>Search hybrid index across tags & FAISS embeddings</span>
          <span>Press ESC to exit</span>
        </div>
      </div>
    </div>
  );
}
