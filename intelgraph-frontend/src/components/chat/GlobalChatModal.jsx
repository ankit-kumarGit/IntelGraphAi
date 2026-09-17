import React, { useState, useRef, useEffect } from 'react';
import { 
  X, 
  Sparkles, 
  Send, 
  ExternalLink, 
  FileText, 
  CheckCircle2, 
  ShieldCheck,
  RotateCcw,
  BookOpen,
  Cpu,
  Layers,
  HelpCircle,
  AlertTriangle
} from 'lucide-react';
import { api } from '../../services/api';
import EvidenceDrawer from '../common/EvidenceDrawer';

// Lightweight, resilient Markdown renderer for enterprise AI chat responses
function EnterpriseMarkdown({ content }) {
  if (!content) return null;

  const lines = content.split('\n');
  const elements = [];
  let inTable = false;
  let tableRows = [];
  let inList = false;
  let listItems = [];
  let inOrderedList = false;
  let orderedItems = [];

  const flushTable = (key) => {
    if (tableRows.length === 0) return null;
    const headerRow = tableRows[0];
    const dataRows = tableRows.slice(1).filter(r => !r.every(c => c.trim().match(/^:?-+:?$/)));
    const el = (
      <div key={key} className="my-3 overflow-x-auto rounded-lg border border-slate-800 bg-slate-950/60">
        <table className="w-full text-xs text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-900/80">
              {headerRow.map((h, i) => (
                <th key={i} className="px-3 py-2 text-slate-300 font-semibold font-mono text-[11px] uppercase tracking-wider">
                  {renderInlineFormatting(h.trim())}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-850">
            {dataRows.map((row, rIdx) => (
              <tr key={rIdx} className="hover:bg-slate-900/40 transition-colors">
                {row.map((cell, cIdx) => (
                  <td key={cIdx} className="px-3 py-2 text-slate-300">
                    {renderInlineFormatting(cell.trim())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
    tableRows = [];
    inTable = false;
    return el;
  };

  const flushList = (key) => {
    if (listItems.length === 0) return null;
    const el = (
      <ul key={key} className="my-2 space-y-1 pl-5 list-disc text-slate-300 text-xs leading-relaxed">
        {listItems.map((item, idx) => (
          <li key={idx}>{renderInlineFormatting(item)}</li>
        ))}
      </ul>
    );
    listItems = [];
    inList = false;
    return el;
  };

  const flushOrderedList = (key) => {
    if (orderedItems.length === 0) return null;
    const el = (
      <ol key={key} className="my-2 space-y-1.5 pl-5 list-decimal text-slate-300 text-xs leading-relaxed">
        {orderedItems.map((item, idx) => (
          <li key={idx}>{renderInlineFormatting(item)}</li>
        ))}
      </ol>
    );
    orderedItems = [];
    inOrderedList = false;
    return el;
  };

  lines.forEach((line, idx) => {
    const trimmed = line.trim();

    // Table row detection
    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      if (inList) elements.push(flushList(`list-${idx}`));
      if (inOrderedList) elements.push(flushOrderedList(`olist-${idx}`));
      inTable = true;
      const cells = trimmed.slice(1, -1).split('|');
      tableRows.push(cells);
      return;
    } else if (inTable) {
      elements.push(flushTable(`table-${idx}`));
    }

    // Unordered List detection
    if (trimmed.match(/^[-*]\s+/)) {
      if (inOrderedList) elements.push(flushOrderedList(`olist-${idx}`));
      inList = true;
      listItems.push(trimmed.replace(/^[-*]\s+/, ''));
      return;
    } else if (inList && trimmed === '') {
      elements.push(flushList(`list-${idx}`));
    } else if (inList && !trimmed.match(/^[-*]\s+/)) {
      elements.push(flushList(`list-${idx}`));
    }

    // Ordered List detection
    if (trimmed.match(/^\d+\.\s+/)) {
      if (inList) elements.push(flushList(`list-${idx}`));
      inOrderedList = true;
      orderedItems.push(trimmed.replace(/^\d+\.\s+/, ''));
      return;
    } else if (inOrderedList && trimmed === '') {
      elements.push(flushOrderedList(`olist-${idx}`));
    } else if (inOrderedList && !trimmed.match(/^\d+\.\s+/)) {
      elements.push(flushOrderedList(`olist-${idx}`));
    }

    if (trimmed === '') {
      return;
    }

    // Horizontal rule
    if (trimmed.match(/^---|^___/)) {
      elements.push(<hr key={idx} className="my-3 border-slate-800" />);
      return;
    }

    // Blockquote / Alert
    if (trimmed.startsWith('>')) {
      const quoteText = trimmed.replace(/^>\s*/, '');
      const isWarning = quoteText.includes('⚠') || quoteText.toLowerCase().includes('governance');
      elements.push(
        <div key={idx} className={`my-2 p-3 rounded-lg border text-xs leading-relaxed ${
          isWarning ? 'bg-amber-950/20 border-amber-500/30 text-amber-200' : 'bg-slate-900/70 border-slate-800 text-slate-300'
        }`}>
          {renderInlineFormatting(quoteText)}
        </div>
      );
      return;
    }

    // Headings
    if (trimmed.startsWith('### ')) {
      elements.push(
        <h4 key={idx} className="text-xs font-mono font-bold uppercase tracking-wider text-brand-400 mt-3 mb-1.5 flex items-center gap-1.5">
          <span>{renderInlineFormatting(trimmed.slice(4))}</span>
        </h4>
      );
      return;
    }
    if (trimmed.startsWith('## ')) {
      elements.push(
        <h3 key={idx} className="text-sm font-bold text-white mt-3.5 mb-1.5">
          {renderInlineFormatting(trimmed.slice(3))}
        </h3>
      );
      return;
    }
    if (trimmed.startsWith('# ')) {
      elements.push(
        <h2 key={idx} className="text-base font-bold text-white mt-4 mb-2">
          {renderInlineFormatting(trimmed.slice(2))}
        </h2>
      );
      return;
    }

    // Standard Paragraph
    elements.push(
      <p key={idx} className="my-1.5 text-xs text-slate-200 leading-relaxed font-sans">
        {renderInlineFormatting(trimmed)}
      </p>
    );
  });

  if (inTable) elements.push(flushTable('table-end'));
  if (inList) elements.push(flushList('list-end'));
  if (inOrderedList) elements.push(flushOrderedList('olist-end'));

  return <div className="space-y-1">{elements}</div>;
}

function renderInlineFormatting(text) {
  if (!text) return text;

  // Split on bold (**...**) and inline code (`...`)
  const parts = [];
  let cur = text;
  let keyIdx = 0;

  // Simple sequential parsing for **bold** and `code` and *italic*
  const tokens = cur.split(/(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g);
  return tokens.map((tok, i) => {
    if (tok.startsWith('**') && tok.endsWith('**')) {
      return <strong key={i} className="font-semibold text-white">{tok.slice(2, -2)}</strong>;
    }
    if (tok.startsWith('`') && tok.endsWith('`')) {
      return <code key={i} className="px-1.5 py-0.5 rounded bg-slate-900 text-brand-300 font-mono text-[11px] border border-slate-800">{tok.slice(1, -1)}</code>;
    }
    if (tok.startsWith('*') && tok.endsWith('*')) {
      return <em key={i} className="italic text-slate-300">{tok.slice(1, -1)}</em>;
    }
    return tok;
  });
}

export default function GlobalChatModal({ isOpen, onClose, defaultAssetTag, currentRole = 'Maintenance Engineer', siteName = 'Plant A', onOpenDocViewer }) {
  const [query, setQuery] = useState('');
  const [scopeFilter, setScopeFilter] = useState('Auto'); // 'Auto' | 'Current Machine' | 'Fleet' | 'Organization' | 'General Engineering Knowledge'
  const [evidenceDrawerOpen, setEvidenceDrawerOpen] = useState(false);
  const [selectedEvidence, setSelectedEvidence] = useState(null);
  const chatBottomRef = useRef(null);

  const [messages, setMessages] = useState([
    {
      sender: 'assistant',
      role: 'assistant',
      agentName: 'IntelGraph AI',
      scope: 'GENERAL',
      answer: 'Hello! I am **IntelGraph AI**, your enterprise industrial operations and asset intelligence assistant.\n\nI can assist you with:\n- **General Engineering Knowledge**: Turbomachinery principles, rotodynamics, tribology, predictive maintenance, vibration standards (ISO 10816-3), and RCA methodologies.\n- **Customer Industrial Records**: Grounded machine telemetry, work orders, OEM technical manuals, SOP procedures, and P&ID engineering drawings.\n- **Hybrid Asset Reasoning**: Evaluating plant physical assets against universal engineering degradation mechanisms.\n- **Fleet Comparative Analysis**: Cross-asset maintenance and reliability tracking.\n\nHow can I support your operational workflow today?',
      citations: [],
      confidence: null
    }
  ]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  if (!isOpen) return null;

  const handleClearHistory = () => {
    setMessages([
      {
        sender: 'assistant',
        role: 'assistant',
        agentName: 'IntelGraph AI',
        scope: 'GENERAL',
        answer: 'Conversation context reset. You can ask any new question across general engineering principles, customer machinery records, or hybrid root cause investigations.',
        citations: [],
        confidence: null
      }
    ]);
  };

  const handleSend = async (customQuery) => {
    const q = (customQuery || query).trim();
    if (!q) return;

    // 1. Build conversation history payload from existing messages
    const conversationHistory = messages.map((m) => ({
      role: m.sender === 'user' ? 'user' : 'assistant',
      content: m.text || m.answer || ''
    }));

    const userMsg = { sender: 'user', role: 'user', text: q };
    setMessages((prev) => [...prev, userMsg]);
    setQuery('');
    setLoading(true);

    try {
      // === ASSET PRECEDENCE FIX ===
      // In 'Auto' mode, QUE must resolve the asset from the query text.
      // Sending the currently selected machine as asset_tag would override QUE's
      // explicit asset detection (e.g. "What is P-194?" while TEST-FINAL-001 is open).
      //
      // Precedence:
      //   'Current Machine' → hard-scope to selected asset (user explicitly chose this)
      //   'Auto'            → send null; backend QUE detects explicit asset from query
      //                       pass selected machine as context_asset_tag only (for pronoun resolution)
      //   'General Knowledge' → no asset scope (handled server-side by scope_filter)
      let effectiveAssetTag = null;
      let contextAssetTag = defaultAssetTag || null;
      if (scopeFilter === 'Current Machine') {
        effectiveAssetTag = defaultAssetTag || null;
        contextAssetTag = null; // not needed — already hard-scoped
      }
      // Auto mode: effectiveAssetTag stays null; QUE resolves from query

      // Call backend API passing conversational history and explicit scope filter
      const res = await api.chat(
        q,
        effectiveAssetTag,       // null in Auto mode → QUE resolves asset from query
        currentRole,
        true,
        conversationHistory,
        scopeFilter,
        contextAssetTag          // context only (used for pronoun resolution, not retrieval scoping)
      );
      
      const botMsg = {
        sender: 'assistant',
        role: 'assistant',
        agentName: res.agent_name || 'IntelGraph AI',
        answer: res.answer,
        scope: res.scope,
        responseFormat: res.response_format,
        citations: res.citations || [],
        confidence: res.confidence, // null for General queries
        refused: res.refused,
        evidenceSummary: res.evidence_summary || []
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          role: 'assistant',
          agentName: 'IntelGraph AI',
          scope: 'GENERAL',
          answer: 'Unable to communicate with IntelGraph AI services: ' + err.message,
          citations: [],
          confidence: null
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const samplePrompts = [
    'What is predictive maintenance?',
    'What is a machine?',
    'What is P-101 and what does it do?',
    'Explain pump failure modes & which apply to P-101',
    'Compare P-101 and P-102 maintenance history',
    'What is the calibration frequency of transmitter X-99?'
  ];

  const handleOpenEvidence = (citations) => {
    const list = citations.map((c) => ({
      document_name: c.document_name,
      document_id: c.document_id,
      date: c.record_date || 'Verified Record',
      page: c.page_number,
      section: c.section_title,
      status: c.governance_status || 'Approved',
      version: c.version || 'v1.0',
      excerpt: c.excerpt || `Verified excerpt from ${c.document_name}, Section ${c.section_title}, Page ${c.page_number}.`
    }));
    setSelectedEvidence(list);
    setEvidenceDrawerOpen(true);
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-3 sm:p-6 animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl h-[88vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Top Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-brand-500/15 text-brand-400 border border-brand-500/30 shadow-inner">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white tracking-tight">IntelGraph AI</h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-medium">
                  Unified Enterprise AI
                </span>
              </div>
              <p className="text-xs text-slate-400">
                General Engineering Intelligence &amp; Verified Industrial Asset Brain
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            {/* Scope Selector: Available Context != Forced Retrieval */}
            <div className="flex items-center gap-1.5 bg-slate-850 px-2.5 py-1 rounded-lg border border-slate-750">
              <span className="text-[11px] text-slate-400 font-mono">Ask about:</span>
              <select
                value={scopeFilter}
                onChange={(e) => setScopeFilter(e.target.value)}
                className="bg-transparent text-xs text-brand-300 font-medium focus:outline-none cursor-pointer"
                title="Knowledge Scope Arbitration"
              >
                <option value="Auto" className="bg-slate-900 text-white">Auto (Intelligent Detection)</option>
                <option value="Current Machine" className="bg-slate-900 text-white">Current Machine ({defaultAssetTag || 'P-101'})</option>
                <option value={`Fleet / ${siteName}`} className="bg-slate-900 text-white">Fleet / {siteName}</option>
                <option value="Organization" className="bg-slate-900 text-white">Organization</option>
                <option value="General Engineering Knowledge" className="bg-slate-900 text-white">General Engineering Knowledge</option>
              </select>
            </div>

            {/* Reset Memory / Thread */}
            <button
              onClick={handleClearHistory}
              title="Reset conversation context"
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-750 text-slate-400 hover:text-white transition-all text-xs flex items-center gap-1 border border-slate-700/60"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">New Thread</span>
            </button>

            {/* Close Button */}
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-all"
              aria-label="Close Assistant"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Quick Question Chips */}
        <div className="px-4 py-2 bg-slate-950/80 border-b border-slate-800/80 flex items-center gap-2 overflow-x-auto scrollbar-thin">
          <span className="text-[10px] text-slate-400 uppercase font-mono font-semibold shrink-0 flex items-center gap-1">
            <HelpCircle className="w-3 h-3 text-brand-400" />
            Suggested:
          </span>
          {samplePrompts.map((p, i) => (
            <button
              key={i}
              onClick={() => handleSend(p)}
              disabled={loading}
              className="px-2.5 py-1 rounded-md bg-slate-850 hover:bg-slate-800 text-slate-300 hover:text-brand-300 text-[11px] whitespace-nowrap border border-slate-750 transition-all shrink-0 hover:border-brand-500/40"
            >
              {p}
            </button>
          ))}
        </div>

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4 text-xs">
          {messages.map((m, idx) => {
            const isUser = m.sender === 'user';
            const hasCitations = m.citations && m.citations.length > 0;
            const isRefusal = m.refused || m.scope === 'UNSUPPORTED' || m.scope === 'UNSUPPORTED_CUSTOMER';

            return (
              <div
                key={idx}
                className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
              >
                {isUser ? (
                  <div className="max-w-xl p-3.5 rounded-2xl bg-brand-600 text-white rounded-tr-none text-xs leading-relaxed shadow-md shadow-brand-900/20 font-sans">
                    {m.text}
                  </div>
                ) : (
                  <div className={`max-w-3xl w-full p-4 sm:p-5 rounded-2xl text-slate-200 rounded-tl-none space-y-3.5 transition-all ${
                    isRefusal 
                      ? 'bg-slate-950 border border-amber-500/30' 
                      : 'bg-slate-950/90 border border-slate-800 shadow-lg'
                  }`}>
                    {/* Header line for Assistant */}
                    <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                      <div className="flex items-center gap-2">
                        <div className="p-1 rounded bg-brand-500/15 text-brand-400">
                          <Sparkles className="w-3.5 h-3.5" />
                        </div>
                        <span className="font-bold text-xs text-white">IntelGraph AI</span>
                        {m.scope && m.scope !== 'GENERAL' && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono uppercase font-semibold bg-slate-900 border border-slate-800 text-slate-400">
                            {m.scope.replace('_', ' ')}
                          </span>
                        )}
                      </div>

                      {/* Confidence badge: ONLY displayed when evidence-grounded, NEVER for purely general questions */}
                      {m.confidence && (
                        <div className="flex items-center gap-1.5 text-[11px] font-mono">
                          <span className={`px-2 py-0.5 rounded border text-[10px] font-medium flex items-center gap-1 ${
                            m.confidence === 'High'
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                              : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                          }`}>
                            <ShieldCheck className="w-3 h-3" />
                            {m.confidence} Confidence
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Conversational Markdown Body */}
                    <div className="text-slate-200 text-xs sm:text-[13px] leading-relaxed font-sans">
                      <EnterpriseMarkdown content={m.answer} />
                    </div>

                    {/* Verified Evidence Footer (Clean Pill Bar - Displayed when primary sources are cited) */}
                    {hasCitations && (
                      <div className="pt-3 border-t border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1">
                            <BookOpen className="w-3 h-3 text-brand-400" />
                            Verified Sources:
                          </span>
                          {m.citations.slice(0, 3).map((cit, cIdx) => (
                            <button
                              key={cIdx}
                              onClick={() => handleOpenEvidence(m.citations)}
                              className="px-2 py-0.5 rounded bg-slate-900 hover:bg-slate-850 border border-slate-800 text-slate-300 hover:text-brand-300 text-[11px] font-mono transition-colors flex items-center gap-1"
                              title={`View ${cit.document_name}, Page ${cit.page_number}`}
                            >
                              <FileText className="w-3 h-3 text-slate-400" />
                              <span className="truncate max-w-[180px]">{cit.document_name}</span>
                              <span className="text-slate-400 font-sans">p.{cit.page_number}</span>
                            </button>
                          ))}
                          {m.citations.length > 3 && (
                            <span className="text-[10px] text-slate-400 font-mono">
                              +{m.citations.length - 3} more
                            </span>
                          )}
                        </div>

                        <button
                          onClick={() => handleOpenEvidence(m.citations)}
                          className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-850 border border-slate-750 text-brand-400 hover:text-brand-300 text-xs font-semibold flex items-center gap-1.5 transition-all self-start sm:self-auto shrink-0"
                        >
                          <span>Evidence Drawer</span>
                          <ExternalLink className="w-3 h-3" />
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}

          {loading && (
            <div className="flex items-center gap-3 text-slate-400 text-xs p-4 bg-slate-950/60 rounded-xl border border-slate-800/60 max-w-md">
              <div className="w-4 h-4 border-2 border-brand-400 border-t-transparent rounded-full animate-spin"></div>
              <span>Querying IntelGraph AI...</span>
            </div>
          )}
          <div ref={chatBottomRef} />
        </div>

        {/* Safety Disclaimer Footer */}
        <div className="px-4 py-1.5 bg-slate-950 border-t border-slate-800 text-[10px] text-slate-400 flex items-center justify-between font-mono">
          <span className="flex items-center gap-1 text-slate-400">
            <AlertTriangle className="w-3 h-3 text-amber-400" />
            Decision support only — verify with approved site procedures before performing field work.
          </span>
          <span className="text-emerald-400 hidden sm:inline">Grounded in Verified Records</span>
        </div>

        {/* Input Bar */}
        <div className="p-3 sm:p-4 border-t border-slate-800 bg-slate-950 flex items-center gap-2.5">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Ask question about machinery records, failure analysis, or general engineering principles..."
            className="flex-1 px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-brand-500 font-sans"
            disabled={loading}
          />
          <button
            onClick={() => handleSend()}
            disabled={loading || !query.trim()}
            className="px-4 py-2.5 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-bold text-xs flex items-center gap-1.5 transition-all shadow-md shadow-brand-500/20 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Send className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Send</span>
          </button>
        </div>
      </div>

      {/* Evidence Drawer */}
      <EvidenceDrawer
        isOpen={evidenceDrawerOpen}
        onClose={() => setEvidenceDrawerOpen(false)}
        evidenceData={selectedEvidence}
        onOpenDocViewer={onOpenDocViewer}
      />
    </div>
  );
}
