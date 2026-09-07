import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Upload, 
  ExternalLink, 
  ShieldCheck, 
  AlertTriangle, 
  Clock, 
  Check, 
  RotateCw,
  Plus
} from 'lucide-react';
import { api } from '../../services/api';
import DocumentViewerModal from '../documents/DocumentViewerModal';

export default function TabDocuments({ assetTag, onOpenUpload }) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [updatingId, setUpdatingId] = useState(null);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const data = await api.getDocuments({ asset_tag: assetTag });
      setDocuments(data);
    } catch (err) {
      console.error('Failed to load documents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, [assetTag]);

  const handleToggleGovernance = async (doc) => {
    const newStatus = doc.governance_status === 'Approved' ? 'Obsolete' : 'Approved';
    const form = new FormData();
    form.append('status', newStatus);
    setUpdatingId(doc.document_id);
    try {
      await api.updateGovernance(doc.document_id, form);
      await loadDocuments();
    } catch (e) {
      alert('Failed to update governance: ' + e.message);
    } finally {
      setUpdatingId(null);
    }
  };

  return (
    <div className="space-y-4">
      {/* Top Bar */}
      <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
        <div>
          <h3 className="font-bold text-white text-sm">Governed Document Library</h3>
          <p className="text-slate-400 text-[11px]">
            {documents.length} Controlled documents associated with {assetTag}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onOpenUpload}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white font-semibold transition-all shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Upload Document</span>
          </button>
        </div>
      </div>

      {/* Documents Table */}
      {loading ? (
        <div className="p-12 text-center text-slate-400">
          <div className="w-8 h-8 border-2 border-brand-400 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
          Loading document library...
        </div>
      ) : documents.length === 0 ? (
        <div className="p-12 text-center text-slate-400 bg-slate-900/50 rounded-xl border border-slate-800">
          <FileText className="w-8 h-8 text-slate-400 mx-auto mb-2 opacity-50" />
          <h4 className="text-sm font-semibold text-slate-300">No Documents Uploaded</h4>
          <p className="text-xs text-slate-400 mt-1">Upload the OEM manual or initial SOP to start building knowledge for this machine.</p>
        </div>
      ) : (
        <div className="rounded-xl border border-slate-800 bg-slate-900/80 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950 text-slate-400 font-mono text-[11px]">
                  <th className="py-3 px-4">Document Title</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Version</th>
                  <th className="py-3 px-4">Effective Date</th>
                  <th className="py-3 px-4">Review Date</th>
                  <th className="py-3 px-4">Governance</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {documents.map((doc) => {
                  const isApproved = doc.governance_status === 'Approved';
                  const isObsolete = doc.governance_status === 'Obsolete';

                  return (
                    <tr
                      key={doc.document_id}
                      className={`hover:bg-slate-800/40 transition-colors ${
                        isObsolete ? 'opacity-60 bg-red-950/10' : ''
                      }`}
                    >
                      <td className="py-3 px-4">
                        <div className="font-semibold text-white flex items-center gap-2">
                          <FileText className={`w-3.5 h-3.5 ${isApproved ? 'text-brand-400' : 'text-red-400'}`} />
                          <span className={isObsolete ? 'line-through text-slate-400' : ''}>
                            {doc.title || doc.filename}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                          {doc.filename} ({doc.chunk_count} Chunks)
                        </div>
                      </td>

                      <td className="py-3 px-4 text-slate-300">
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-medium text-[11px]">
                          {doc.category}
                        </span>
                      </td>

                      <td className="py-3 px-4 font-mono text-slate-300">
                        {doc.version}
                      </td>

                      <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">
                        {doc.effective_date || 'N/A'}
                      </td>

                      <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">
                        {doc.review_date || 'N/A'}
                      </td>

                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded uppercase font-semibold ${
                          isApproved
                            ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                            : 'bg-red-500/15 text-red-400 border border-red-500/30'
                        }`}>
                          {isApproved ? <ShieldCheck className="w-3 h-3" /> : <AlertTriangle className="w-3 h-3" />}
                          {doc.governance_status}
                        </span>
                      </td>

                      <td className="py-3 px-4 text-right space-x-2">
                        <button
                          onClick={() => setSelectedDocId(doc.document_id)}
                          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-all"
                        >
                          View Chunks
                        </button>
                        <button
                          onClick={() => handleToggleGovernance(doc)}
                          disabled={updatingId === doc.document_id}
                          className={`px-2 py-1 rounded text-[11px] font-medium transition-all ${
                            isApproved
                              ? 'bg-red-500/15 hover:bg-red-500/25 text-red-400 border border-red-500/30'
                              : 'bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-400 border border-emerald-500/30'
                          }`}
                        >
                          {updatingId === doc.document_id ? (
                            <RotateCw className="w-3 h-3 animate-spin mx-auto" />
                          ) : isApproved ? (
                            'Retire / Obsolete'
                          ) : (
                            'Approve'
                          )}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

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
