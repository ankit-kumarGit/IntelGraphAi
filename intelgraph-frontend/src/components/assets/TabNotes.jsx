import React, { useState } from 'react';
import { User, Send, MessageSquare, AlertCircle } from 'lucide-react';
import { api } from '../../services/api';

export default function TabNotes({ assetTag, notes = [], onNoteAdded, currentRole }) {
  const [newNoteText, setNewNoteText] = useState('');
  const [newNoteAuthor, setNewNoteAuthor] = useState('Field Technician');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newNoteText.trim()) return;
    setSubmitting(true);
    try {
      const form = new FormData();
      form.append('text', newNoteText);
      form.append('author', newNoteAuthor);
      form.append('author_role', currentRole || 'Maintenance Engineer');
      await api.addNote(assetTag, form);
      setNewNoteText('');
      if (onNoteAdded) onNoteAdded();
    } catch (err) {
      alert('Failed to record observation: ' + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Human Input Distinction Banner */}
      <div className="p-3 rounded-xl bg-amber-950/20 border border-amber-500/20 flex items-center justify-between text-xs text-amber-300/90">
        <div className="flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            <strong>[Human Input]</strong> represents operator and technician observations. They are unverified field notes, distinct from authorized engineering records.
          </span>
        </div>
      </div>

      {/* Observation Form */}
      <form onSubmit={handleSubmit} className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3 shadow-lg">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-white text-sm flex items-center gap-2">
            <User className="w-4 h-4 text-amber-400" />
            <span>Record Human Field Observation</span>
          </h3>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30 font-semibold">
            Human Input
          </span>
        </div>

        <textarea
          value={newNoteText}
          onChange={(e) => setNewNoteText(e.target.value)}
          placeholder="e.g. Unusual pitch noise noticed on drive-end coupling during switchover..."
          rows={3}
          required
          className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:border-brand-500"
        />

        <div className="flex items-center justify-between text-xs pt-1">
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Author:</span>
            <input
              type="text"
              value={newNoteAuthor}
              onChange={(e) => setNewNoteAuthor(e.target.value)}
              className="px-2.5 py-1 rounded bg-slate-950 border border-slate-800 text-xs text-slate-200 w-44"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs flex items-center gap-1.5 transition-all shadow-md shadow-amber-500/20 disabled:opacity-50"
          >
            <Send className="w-3.5 h-3.5" />
            <span>Submit Observation</span>
          </button>
        </div>
      </form>

      {/* Notes Stream with Visual Distinction */}
      <div className="space-y-3">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Field Observations ({notes.length})
        </h4>

        {notes.length === 0 ? (
          <p className="text-xs text-slate-400 py-6 text-center">No field observations recorded yet.</p>
        ) : (
          notes.map((n) => (
            <div
              key={n.note_id}
              className="p-4 rounded-xl bg-slate-900 border-l-4 border-l-amber-400 border-y border-r border-slate-800 space-y-2 text-xs"
            >
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-2 text-[11px]">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-white">{n.author}</span>
                  <span className="text-slate-400">({n.author_role})</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-slate-400 font-mono">{n.created_at}</span>
                  <span className="text-[10px] font-mono px-2 py-0.2 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-semibold">
                    Human Input
                  </span>
                </div>
              </div>
              <p className="text-slate-200 leading-relaxed font-sans text-xs">
                "{n.text}"
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
