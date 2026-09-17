import React, { useState, useEffect } from 'react';
import { 
  X, 
  Settings, 
  Archive, 
  RotateCcw, 
  Trash2, 
  AlertTriangle, 
  ShieldAlert, 
  CheckCircle2, 
  Layers, 
  FileText, 
  Activity, 
  Database, 
  Network, 
  Info,
  Loader2,
  Lock
} from 'lucide-react';
import { api } from '../../services/api';

export default function ManageMachineModal({ 
  isOpen, 
  onClose, 
  asset, 
  currentRole, 
  onMachineUpdated, 
  onMachineDeleted 
}) {
  const [activeTab, setActiveTab] = useState('edit'); // edit | archive | delete
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Edit form state
  const [editForm, setEditForm] = useState({
    name: '',
    description: '',
    area: '',
    plant: '',
    criticality: '',
    status: ''
  });

  // Deletion preview state
  const [previewLoading, setPreviewLoading] = useState(false);
  const [deletionPreview, setDeletionPreview] = useState(null);
  const [confirmTag, setConfirmTag] = useState('');

  const isPlatformAdmin = currentRole === 'Platform Administrator' || currentRole === 'Administrator';
  const isArchived = asset?.status === 'Archived';

  useEffect(() => {
    if (asset) {
      setEditForm({
        name: asset.name || '',
        description: asset.description || '',
        area: asset.area || '',
        plant: asset.plant || '',
        criticality: asset.criticality || 'Medium',
        status: asset.status || 'Operational'
      });
      setError(null);
      setSuccessMessage(null);
      setConfirmTag('');
    }
  }, [asset]);

  useEffect(() => {
    if (isOpen && activeTab === 'delete' && asset?.tag && isPlatformAdmin) {
      loadDeletionPreview();
    }
  }, [isOpen, activeTab, asset?.tag, isPlatformAdmin]);

  const loadDeletionPreview = async () => {
    setPreviewLoading(true);
    setError(null);
    try {
      const data = await api.getDeletionPreview(asset.tag);
      setDeletionPreview(data);
    } catch (err) {
      setError('Failed to fetch deletion impact preview: ' + err.message);
    } finally {
      setPreviewLoading(false);
    }
  };

  if (!isOpen || !asset) return null;

  const handleUpdate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.updateMachine(asset.tag, editForm);
      setSuccessMessage(`Machine '${asset.tag}' updated successfully.`);
      if (onMachineUpdated) onMachineUpdated(res);
      setTimeout(() => {
        setSuccessMessage(null);
        onClose();
      }, 1200);
    } catch (err) {
      setError(err.message || 'Failed to update machine');
    } finally {
      setLoading(false);
    }
  };

  const handleArchiveToggle = async () => {
    setLoading(true);
    setError(null);
    try {
      if (isArchived) {
        const res = await api.restoreMachine(asset.tag);
        setSuccessMessage(res.message || `Machine '${asset.tag}' restored.`);
        if (onMachineUpdated) onMachineUpdated({ ...asset, status: 'Operational' });
      } else {
        const res = await api.archiveMachine(asset.tag);
        setSuccessMessage(res.message || `Machine '${asset.tag}' archived.`);
        if (onMachineUpdated) onMachineUpdated({ ...asset, status: 'Archived' });
      }
      setTimeout(() => {
        setSuccessMessage(null);
        onClose();
      }, 1200);
    } catch (err) {
      setError(err.message || 'Failed to toggle archive state');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (confirmTag.trim().toUpperCase() !== asset.tag.toUpperCase()) {
      setError(`Confirmation mismatch: please type '${asset.tag}' to proceed.`);
      return;
    }
    if (!isPlatformAdmin) {
      setError('Permanent deletion is restricted to Platform Administrator.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await api.deleteMachine(asset.tag, confirmTag.trim());
      setSuccessMessage(`Machine '${asset.tag}' permanently deleted across all layers.`);
      if (onMachineDeleted) onMachineDeleted(asset.tag);
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (err) {
      setError(err.message || 'Cascade deletion failed. See server logs for layer verification report.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-brand-500/10 border border-brand-500/20 text-brand-400">
              <Settings className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-white">Manage Machine: {asset.tag}</h3>
                <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                  isArchived 
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' 
                    : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                }`}>
                  {asset.status || 'Active'}
                </span>
              </div>
              <p className="text-xs text-slate-400">{asset.name}</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Tabs Strip */}
        <div className="flex items-center border-b border-slate-800 bg-slate-950/40 px-5 gap-2">
          <button
            onClick={() => setActiveTab('edit')}
            className={`py-3 px-3 text-xs font-semibold border-b-2 flex items-center gap-2 transition ${
              activeTab === 'edit'
                ? 'border-brand-400 text-brand-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Settings className="w-3.5 h-3.5" />
            Edit Machine
          </button>
          <button
            onClick={() => setActiveTab('archive')}
            className={`py-3 px-3 text-xs font-semibold border-b-2 flex items-center gap-2 transition ${
              activeTab === 'archive'
                ? 'border-amber-400 text-amber-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            {isArchived ? <RotateCcw className="w-3.5 h-3.5" /> : <Archive className="w-3.5 h-3.5" />}
            {isArchived ? 'Restore' : 'Archive'}
          </button>
          <button
            onClick={() => setActiveTab('delete')}
            className={`py-3 px-3 text-xs font-semibold border-b-2 flex items-center gap-1.5 transition ml-auto ${
              activeTab === 'delete'
                ? 'border-red-500 text-red-400'
                : 'border-transparent text-red-400/70 hover:text-red-300'
            }`}
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Permanently Delete</span>
            {!isPlatformAdmin && <span className="text-xs">🔒</span>}
          </button>
        </div>

        {/* Alert / Notification Feedback */}
        {error && (
          <div className="mx-5 mt-4 p-3.5 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs flex items-center gap-2.5">
            <AlertTriangle className="w-4 h-4 shrink-0 text-red-400" />
            <span>{error}</span>
          </div>
        )}
        {successMessage && (
          <div className="mx-5 mt-4 p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2.5">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
            <span>{successMessage}</span>
          </div>
        )}

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-5 flex-1">
          {/* TAB 1: EDIT MACHINE */}
          {activeTab === 'edit' && (
            <form onSubmit={handleUpdate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Machine Name</label>
                <input
                  type="text"
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-800/80 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-brand-500"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">Plant Facility</label>
                  <input
                    type="text"
                    value={editForm.plant}
                    onChange={(e) => setEditForm({ ...editForm, plant: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-800/80 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">Operating Area</label>
                  <input
                    type="text"
                    value={editForm.area}
                    onChange={(e) => setEditForm({ ...editForm, area: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-800/80 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-brand-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">Criticality Level</label>
                  <select
                    value={editForm.criticality}
                    onChange={(e) => setEditForm({ ...editForm, criticality: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-800/80 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-brand-500"
                  >
                    <option value="Critical">Critical</option>
                    <option value="High">High</option>
                    <option value="Medium">Medium</option>
                    <option value="Low">Low</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">Operating Status</label>
                  <select
                    value={editForm.status}
                    onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-800/80 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-brand-500"
                  >
                    <option value="Operational">Operational</option>
                    <option value="Maintenance Due">Maintenance Due</option>
                    <option value="Under Inspection">Under Inspection</option>
                    <option value="Archived">Archived</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Operational Description</label>
                <textarea
                  value={editForm.description}
                  onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 bg-slate-800/80 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="pt-2 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold flex items-center gap-2 transition disabled:opacity-50"
                >
                  {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  Save Changes
                </button>
              </div>
            </form>
          )}

          {/* TAB 2: ARCHIVE / RESTORE */}
          {activeTab === 'archive' && (
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700 space-y-2">
                <div className="flex items-center gap-2 text-amber-300 font-semibold text-sm">
                  <Info className="w-4 h-4" />
                  <span>Enterprise Archival Semantics</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Archiving a machine is <strong>fully reversible</strong>. It preserves 100% of historical documents, 
                  sensor telemetry, work orders, RCA reports, and statutory inspection certificates for compliance 
                  audits. Archived machines are hidden from the primary active operations view but remain searchable 
                  in historical registers.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="text-xs text-slate-400">Current Lifecycle State:</span>
                  <div className="text-sm font-bold text-white flex items-center gap-2 mt-0.5">
                    <span className={`w-2.5 h-2.5 rounded-full ${isArchived ? 'bg-amber-400' : 'bg-emerald-400'}`} />
                    {isArchived ? 'Archived (Historical/Inactive)' : 'Active (Operational)'}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={handleArchiveToggle}
                  disabled={loading}
                  className={`px-4 py-2 rounded-lg font-semibold text-xs flex items-center gap-2 transition disabled:opacity-50 ${
                    isArchived
                      ? 'bg-emerald-600 hover:bg-emerald-500 text-white'
                      : 'bg-amber-600 hover:bg-amber-500 text-white'
                  }`}
                >
                  {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  {isArchived ? (
                    <>
                      <RotateCcw className="w-4 h-4" />
                      Restore to Active View
                    </>
                  ) : (
                    <>
                      <Archive className="w-4 h-4" />
                      Archive Machine
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* TAB 3: PERMANENTLY DELETE */}
          {activeTab === 'delete' && (
            <div className="space-y-5">
              {/* Danger Zone Alert */}
              <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 space-y-2">
                <div className="flex items-center gap-2 text-red-400 font-bold text-sm">
                  <ShieldAlert className="w-5 h-5" />
                  <span>Permanent Cascade Deletion (Danger Zone)</span>
                </div>
                <p className="text-xs text-red-200/90 leading-relaxed">
                  Permanent deletion will trigger a multi-layer cascade saga across MongoDB, Neo4j, Qdrant, FAISS, 
                  and local storage. This action is <strong>strictly irreversible</strong> and restricted to 
                  <strong> Platform Administrator</strong> privileges.
                </p>
              </div>

              {!isPlatformAdmin ? (
                /* LOCKED GOVERNANCE VIEW FOR OPERATIONAL USERS */
                <div className="space-y-4">
                  <div className="p-6 rounded-2xl bg-slate-950/80 border border-slate-800 text-center flex flex-col items-center justify-center space-y-3">
                    <div className="w-14 h-14 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
                      <Lock className="w-7 h-7" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white">Permanent Deletion Restricted</h4>
                      <p className="text-xs text-slate-300 mt-1 max-w-md leading-relaxed">
                        Permanent machine deletion is strictly restricted to <strong>Platform Administrator</strong>.
                      </p>
                      <p className="text-[11px] text-slate-500 mt-1">
                        Your active role is <strong>{currentRole || 'Operational User'}</strong>. Operational roles do not have permission to execute cascade deletions.
                      </p>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-slate-800/40 border border-slate-800 text-xs text-slate-400 flex items-start gap-2.5">
                    <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                    <span>
                      Operational governance policy strictly prevents permanent deletion attempts. All delete requests are denied server-side with <strong>HTTP 403 Forbidden</strong> before any storage layer is modified.
                    </span>
                  </div>

                  <div className="pt-2 flex justify-end">
                    <button
                      type="button"
                      onClick={onClose}
                      className="px-5 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
                    >
                      Close
                    </button>
                  </div>
                </div>
              ) : (
                /* AUTHORIZED PLATFORM ADMINISTRATOR WORKFLOW */
                <div className="space-y-5">
                  {/* Live Impact Preview */}
                  <div className="space-y-2.5">
                    <div className="flex items-center justify-between text-xs text-slate-300 font-semibold">
                      <span>Live Deletion Impact Preview:</span>
                      {previewLoading && (
                        <span className="flex items-center gap-1.5 text-slate-400 font-normal">
                          <Loader2 className="w-3.5 h-3.5 animate-spin" /> Fetching live counts...
                        </span>
                      )}
                    </div>

                    {deletionPreview ? (
                      <div className="grid grid-cols-3 gap-2.5 text-xs">
                        <div className="p-3 rounded-lg bg-slate-800/60 border border-slate-700/60">
                          <span className="text-slate-400 block">Documents & Chunks</span>
                          <strong className="text-base text-white">
                            {deletionPreview.counts.documents} docs / {deletionPreview.counts.document_chunks} chunks
                          </strong>
                          <span className="text-[10px] text-slate-400 block mt-0.5">
                            Exclusive: {deletionPreview.counts.exclusive_files} | Shared: {deletionPreview.counts.shared_files}
                          </span>
                        </div>

                        <div className="p-3 rounded-lg bg-slate-800/60 border border-slate-700/60">
                          <span className="text-slate-400 block">Telemetry & Events</span>
                          <strong className="text-base text-white">
                            {deletionPreview.counts.telemetry_points} points
                          </strong>
                          <span className="text-[10px] text-slate-400 block mt-0.5">
                            WO: {deletionPreview.counts.maintenance_records} | Insp: {deletionPreview.counts.inspection_records}
                          </span>
                        </div>

                        <div className="p-3 rounded-lg bg-slate-800/60 border border-slate-700/60">
                          <span className="text-slate-400 block">AI & Graph Topology</span>
                          <strong className="text-base text-white">
                            {deletionPreview.counts.neo4j_nodes} nodes / {deletionPreview.counts.neo4j_edges} edges
                          </strong>
                          <span className="text-[10px] text-slate-400 block mt-0.5">
                            Vectors: {deletionPreview.counts.qdrant_vectors} Qdrant
                          </span>
                        </div>
                      </div>
                    ) : !previewLoading ? (
                      <button
                        type="button"
                        onClick={loadDeletionPreview}
                        className="text-xs text-brand-400 underline hover:text-brand-300"
                      >
                        Load Live Deletion Preview
                      </button>
                    ) : null}

                    <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-[11px] text-slate-400 space-y-1">
                      <div className="flex items-center gap-1.5 text-slate-300 font-medium">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                        <span>Shared Data Safety Guarantees:</span>
                      </div>
                      <ul className="list-disc list-inside space-y-0.5 text-slate-400 pl-1">
                        <li>Global industrial ontology concepts (e.g. <em>Centrifugal Pump, SKF Bearing</em>) are <strong>strictly preserved</strong>.</li>
                        <li>Documents shared with other machines will only be unlinked; physical files and shared vector points are <strong>not deleted</strong>.</li>
                        <li>Permanent <code>MACHINE_DELETED</code> audit event is permanently preserved in the immutable audit log.</li>
                      </ul>
                    </div>
                  </div>

                  {/* Confirmation Input Field */}
                  <div className="pt-2 border-t border-slate-800 space-y-2">
                    <label className="block text-xs font-semibold text-slate-300">
                      To confirm permanent deletion, type <span className="font-mono text-red-400 font-bold">{asset.tag}</span> below:
                    </label>
                    <input
                      type="text"
                      value={confirmTag}
                      onChange={(e) => setConfirmTag(e.target.value)}
                      placeholder={asset.tag}
                      className="w-full px-3 py-2 bg-slate-950 border border-red-500/40 rounded-lg text-sm text-white font-mono focus:outline-none focus:border-red-500"
                    />
                  </div>

                  {/* Delete Action Button */}
                  <div className="pt-2 flex justify-end gap-3">
                    <button
                      type="button"
                      onClick={onClose}
                      className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={handleDelete}
                      disabled={
                        loading || 
                        !isPlatformAdmin || 
                        confirmTag.trim().toUpperCase() !== asset.tag.toUpperCase()
                      }
                      className="px-5 py-2.5 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-bold flex items-center gap-2 transition disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-red-600/20"
                    >
                      {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                      <Trash2 className="w-4 h-4" />
                      Permanently Delete Machine
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
