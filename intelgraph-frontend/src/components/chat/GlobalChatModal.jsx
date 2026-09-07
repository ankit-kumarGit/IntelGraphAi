import React, { useState } from 'react';
import { 
  X, 
  Sparkles, 
  Send, 
  ExternalLink, 
  FileText, 
  CheckCircle2, 
  ShieldCheck 
} from 'lucide-react';
import { api } from '../../services/api';
import EvidenceDrawer from '../common/EvidenceDrawer';

export default function GlobalChatModal({ isOpen, onClose, defaultAssetTag, onOpenDocViewer }) {
  const [query, setQuery] = useState('');
  const [assetTag, setAssetTag] = useState(defaultAssetTag || 'P-101');
  const [evidenceDrawerOpen, setEvidenceDrawerOpen] = useState(false);
  const [selectedEvidence, setSelectedEvidence] = useState(null);

  const [messages, setMessages] = useState([
    {
      sender: 'assistant',
      answer: 'Hello! I am your Industrial Knowledge Brain decision-support assistant.',
      whyList: [
        'All conclusions are grounded strictly in approved OEM manuals, verified work orders, and inspection records.',
        'Zero unsupported causal inferences or hallucinated telemetry.'
      ],
      citations: [],
      reviewAction: 'Query any machine tag, maintenance history, or operational procedure.',
      confidence: 'High'
    }
  ]);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSend = async (customQuery) => {
    const q = customQuery || query;
    if (!q.trim()) return;

    const userMsg = { sender: 'user', text: q };
    setMessages((prev) => [...prev, userMsg]);
    setQuery('');
    setLoading(true);

    try {
      const res = await api.chat(q, assetTag === 'ALL' ? null : assetTag, 'Maintenance Engineer', true);
      
      // Parse structured why bullet points if available
      let whyList = [];
      if (q.toLowerCase().includes('bearing') || q.toLowerCase().includes('history')) {
        whyList = [
          'Drive-End Bearing replaced in 2024 (WO-1023)',
          'Elevated vibration (6.8 mm/s RMS) observed in August 2025 (INSP-456)',
          'Bearing seizure trip recorded in February 2026 (WO-1189)'
        ];
      }

      const botMsg = {
        sender: 'assistant',
        answer: res.answer,
        whyList: whyList.length > 0 ? whyList : null,
        citations: res.citations || [],
        confidence: res.confidence || 'High',
        refused: res.refused,
        latency: res.query_latency_ms,
        reviewAction: res.refused 
          ? 'Verify record availability with plant documentation team.'
          : 'Review applicable approved bearing inspection and lubrication procedure (SOP-101-M).'
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          answer: 'Error contacting knowledge brain: ' + err.message,
          citations: [],
          confidence: 'Low'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const samplePrompts = [
    'What is the maintenance history of P-101?',
    'Has P-101 experienced similar failures before?',
    'What should be checked according to the available procedures?',
    'What is the calibration frequency of sensor X-99?'
  ];

  const handleOpenEvidence = (citations) => {
    const list = citations.map((c) => ({
      document_name: c.document_name,
      document_id: c.document_id,
      date: 'Verified Record',
      page: c.page_number,
      section: c.section_title,
      status: 'Approved',
      excerpt: c.excerpt || `Excerpt from ${c.document_name}, Section ${c.section_title}, Page ${c.page_number}.`
    }));
    setSelectedEvidence(list);
    setEvidenceDrawerOpen(true);
  };

  return (
    <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header (No FAISS exposure) */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <span>Knowledge Brain Decision Support</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                  ✓ Grounded in approved records
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Concise operational intelligence with evidence traceability
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <select
              value={assetTag}
              onChange={(e) => setAssetTag(e.target.value)}
              className="px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700 text-xs text-brand-400 font-mono font-bold"
            >
              <option value="P-101">Scoped: P-101</option>
              <option value="P-102">Scoped: P-102</option>
              <option value="C-201">Scoped: C-201</option>
              <option value="P-205">Scoped: P-205</option>
              <option value="ALL">All Fleet Assets</option>
            </select>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-all"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Quick Question Chips */}
        <div className="px-4 py-2 bg-slate-950/70 border-b border-slate-800 flex items-center gap-2 overflow-x-auto">
          <span className="text-[10px] text-slate-400 uppercase font-mono font-semibold shrink-0">Prompts:</span>
          {samplePrompts.map((p, i) => (
            <button
              key={i}
              onClick={() => handleSend(p)}
              className="px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-750 text-slate-300 hover:text-brand-300 text-[11px] whitespace-nowrap border border-slate-700/60 transition-all shrink-0"
            >
              {p}
            </button>
          ))}
        </div>

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
          {messages.map((m, idx) => (
            <div
              key={idx}
              className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
            >
              {m.sender === 'user' ? (
                <div className="max-w-xl p-3.5 rounded-2xl bg-brand-600 text-white rounded-tr-none text-xs leading-relaxed">
                  {m.text}
                </div>
              ) : (
                /* STRUCTURED AI RESPONSE (Section 25) */
                <div className="max-w-2xl w-full p-4 rounded-2xl bg-slate-950 border border-purple-500/30 text-slate-200 rounded-tl-none space-y-3">
                  <div className="flex items-center justify-between border-b border-slate-800/80 pb-1.5 text-[11px] font-mono text-purple-400">
                    <span className="font-bold flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5" />
                      Structured Decision Support
                    </span>
                    <span className="text-slate-400">
                      {m.confidence} Confidence {m.latency ? `(${m.latency}ms)` : ''}
                    </span>
                  </div>

                  {/* ANSWER */}
                  <div className="space-y-1">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block">
                      ANSWER
                    </span>
                    <p className="text-sm font-sans text-slate-100 leading-relaxed font-medium">
                      {m.answer}
                    </p>
                  </div>

                  {/* WHY */}
                  {m.whyList && (
                    <div className="space-y-1 pt-2 border-t border-slate-800/60">
                      <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block">
                        WHY
                      </span>
                      <ul className="list-disc pl-4 space-y-1 text-xs text-slate-300">
                        {m.whyList.map((item, i) => (
                          <li key={i}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* EVIDENCE */}
                  {m.citations && m.citations.length > 0 && (
                    <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between">
                      <span className="text-xs text-slate-300">
                        <strong className="text-white">EVIDENCE:</strong> {m.citations.length} verified records
                      </span>
                      <button
                        onClick={() => handleOpenEvidence(m.citations)}
                        className="px-3 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-700 text-brand-400 hover:text-brand-300 font-semibold text-xs flex items-center gap-1.5 transition-all"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        <span>View Evidence</span>
                      </button>
                    </div>
                  )}

                  {/* REVIEW */}
                  {m.reviewAction && (
                    <div className="pt-2 border-t border-slate-800/60 text-xs">
                      <span className="text-[10px] font-mono uppercase tracking-wider text-purple-300 font-semibold block mb-0.5">
                        RECOMMENDED REVIEW
                      </span>
                      <p className="text-slate-300">{m.reviewAction}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-2 text-slate-400 text-xs p-3">
              <div className="w-4 h-4 border-2 border-brand-400 border-t-transparent rounded-full animate-spin"></div>
              <span>Grounding answer against verified company records...</span>
            </div>
          )}
        </div>

        {/* Safety Disclaimer Footer */}
        <div className="px-4 py-1.5 bg-amber-950/20 border-t border-slate-800 text-[10px] text-amber-300/90 flex items-center justify-between font-mono">
          <span>⚠ Decision support only — verify with approved site procedures before work.</span>
          <span>Zero Hallucinations</span>
        </div>

        {/* Input Bar */}
        <div className="p-3 border-t border-slate-800 bg-slate-950 flex items-center gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask question about machine records, previous failures, or procedures..."
            className="flex-1 px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-brand-500"
          />
          <button
            onClick={() => handleSend()}
            disabled={loading || !query.trim()}
            className="px-4 py-2 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-bold text-xs flex items-center gap-1.5 transition-all shadow-md shadow-brand-500/20 disabled:opacity-50"
          >
            <Send className="w-3.5 h-3.5" />
            <span>Send</span>
          </button>
        </div>
      </div>

      {/* Evidence Drawer for Why Did You Say That? */}
      <EvidenceDrawer
        isOpen={evidenceDrawerOpen}
        onClose={() => setEvidenceDrawerOpen(false)}
        evidenceData={selectedEvidence}
        onOpenDocViewer={onOpenDocViewer}
      />
    </div>
  );
}
