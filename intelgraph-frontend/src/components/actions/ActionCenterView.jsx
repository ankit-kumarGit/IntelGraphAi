import React, { useState, useEffect } from 'react';
import { 
  AlertCircle, 
  Wrench, 
  ShieldAlert, 
  CheckCircle2, 
  ArrowRight, 
  ChevronDown, 
  ChevronUp, 
  FileText, 
  Clock, 
  User, 
  ShieldCheck, 
  Lock, 
  X, 
  RotateCw,
  ExternalLink,
  Send,
  Layers
} from 'lucide-react';
import { api } from '../../services/api';
import EvidenceDrawer from '../common/EvidenceDrawer';

export default function ActionCenterView({ onSelectAsset, currentRole = 'Maintenance Engineer', currentPersona }) {
  const [actions, setActions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('all');
  const [expandedId, setExpandedId] = useState(null);
  const [evidenceDrawerOpen, setEvidenceDrawerOpen] = useState(false);
  const [selectedEvidence, setSelectedEvidence] = useState(null);

  // Status updating & RBAC state
  const [updatingId, setUpdatingId] = useState(null);
  const [rbacErrorModal, setRbacErrorModal] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // CMMS Dispatch State
  const [dispatchModalAct, setDispatchModalAct] = useState(null);
  const [dispatchSystem, setDispatchSystem] = useState('SAP_PM');
  const [dispatchNotes, setDispatchNotes] = useState('');
  const [dispatching, setDispatching] = useState(false);
  const [dispatchResult, setDispatchResult] = useState(null);

  useEffect(() => {
    let isMounted = true;
    async function loadActions() {
      setLoading(true);
      try {
        const data = await api.getActions();
        if (isMounted) setActions(data);
      } catch (err) {
        console.error('Failed to load action items:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadActions();
    return () => { isMounted = false; };
  }, []);

  const filtered = filterType === 'all' 
    ? actions 
    : actions.filter(a => a.type === filterType);

  const handleOpenEvidence = (act) => {
    setSelectedEvidence([
      {
        document_name: act.evidence || 'Industrial Action Record',
        date: '2026-02-22',
        page: '1',
        status: 'Verified',
        excerpt: `${act.title}: ${act.why_it_matters}`
      }
    ]);
    setEvidenceDrawerOpen(true);
  };

  const handleStatusChange = async (act, newStatus) => {
    if (act.status === newStatus) return;
    setUpdatingId(act.action_id);
    setSuccessMsg(null);
    try {
      const res = await api.updateActionStatus(act.action_id, newStatus, currentRole);
      setActions(prev => prev.map(a => a.action_id === act.action_id ? { ...a, status: newStatus } : a));
      setSuccessMsg(`Action ${act.action_id} updated to '${newStatus}' by ${currentPersona?.name || currentRole}`);
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err) {
      if (err.message.includes('403') || err.message.includes('Permission Denied')) {
        setRbacErrorModal({
          actionId: act.action_id,
          title: act.title,
          attemptedStatus: newStatus,
          userRole: currentRole,
          userName: currentPersona?.name || 'Current User',
          rawError: err.message,
        });
      } else {
        alert('Status update failed: ' + err.message);
      }
    } finally {
      setUpdatingId(null);
    }
  };

  const handleDispatchCmms = async (e) => {
    e.preventDefault();
    if (!dispatchModalAct) return;
    setDispatching(true);
    try {
      const res = await api.exportActionToCmms(
        dispatchModalAct.action_id,
        dispatchSystem,
        dispatchNotes
      );
      setDispatchResult(res);
      setActions(prev => prev.map(a => 
        a.action_id === dispatchModalAct.action_id 
          ? { 
              ...a, 
              cmms_dispatched: true, 
              cmms_reference_id: res.external_reference_id, 
              cmms_target_system: res.target_system 
            }
          : a
      ));
      setSuccessMsg(`Action ${dispatchModalAct.action_id} dispatched to ${res.target_system} (Ref: ${res.external_reference_id})`);
      setTimeout(() => setSuccessMsg(null), 5000);
    } catch (err) {
      alert('CMMS export failed: ' + err.message);
    } finally {
      setDispatching(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Closed':
      case 'Resolved':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'In Progress':
        return 'bg-brand-500/20 text-brand-400 border-brand-500/30';
      case 'Investigating':
        return 'bg-slate-800 text-slate-300 border-slate-700';
      case 'Open':
      default:
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="text-xs font-mono tracking-wider uppercase text-slate-400 font-semibold mb-1">
            Operational Queue & Governance
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <span>Action Center</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Prioritized operational queue of maintenance overhauls, findings, and compliance reviews with server-enforced RBAC
          </p>
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto text-xs">
          {['all', 'Maintenance Due', 'Open Finding', 'Compliance Gap'].map((t) => (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              className={`px-3 py-1.5 rounded-lg capitalize font-medium whitespace-nowrap transition-all ${
                filterType === t
                  ? 'bg-brand-500/15 text-brand-400 border border-brand-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Role Context & Separation of Duties Info */}
      <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between gap-4 text-xs">
        <div className="flex items-center gap-2.5">
          <div className="w-6 h-6 rounded-full bg-brand-500/20 text-brand-400 font-bold font-mono text-xs flex items-center justify-center">
            {currentPersona?.avatar_initials || 'ME'}
          </div>
          <div className="text-slate-300">
            Current Operator: <strong className="text-white">{currentPersona?.name || currentRole}</strong>
            <span className="text-slate-400 ml-2">({currentRole})</span>
          </div>
        </div>

        <div className="text-[11px] font-mono text-slate-400 hidden sm:block">
          {currentRole === 'Maintenance Engineer' && (
            <span className="text-amber-400">Can Investigate / Progress. Closing requires Plant Manager or Admin.</span>
          )}
          {currentRole === 'Plant Manager' && (
            <span className="text-emerald-400">Full operational approval & action resolution authority.</span>
          )}
          {currentRole === 'Quality / Compliance Auditor' && (
            <span className="text-cyan-400">Can audit compliance gaps. Overhaul closure requires Plant Manager.</span>
          )}
          {currentRole === 'Administrator' && (
            <span className="text-brand-400">Global administrative authorization override.</span>
          )}
        </div>
      </div>

      {successMsg && (
        <div className="p-3 rounded-xl bg-emerald-950/30 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2 animate-in fade-in duration-200">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Operational Queue */}
      {loading ? (
        <div className="p-16 text-center text-slate-400">
          <div className="w-8 h-8 border-2 border-brand-400 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          Evaluating operational queue...
        </div>
      ) : filtered.length === 0 ? (
        <div className="p-12 text-center text-slate-400 bg-slate-900/50 rounded-xl border border-slate-800">
          <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2 opacity-50" />
          <h4 className="text-sm font-semibold text-slate-300">All Operations Clear</h4>
          <p className="text-xs text-slate-400 mt-1">No pending maintenance overhauls, open findings, or compliance gaps found.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((act) => {
            const isExpanded = expandedId === act.action_id;
            const isCrit = act.severity === 'Critical';
            const currentStatus = act.status || 'Open';

            return (
              <div
                key={act.action_id}
                className={`rounded-2xl border transition-all ${
                  isCrit
                    ? 'bg-red-950/15 border-red-500/30'
                    : 'bg-slate-900 border-slate-800 hover:border-slate-700'
                }`}
              >
                {/* Collapsed State (Progressive Disclosure) */}
                <div className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="flex items-center gap-3 min-w-0">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase shrink-0 ${
                      isCrit ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400'
                    }`}>
                      {act.severity}
                    </span>

                    <button
                      onClick={() => onSelectAsset(act.asset_tag)}
                      className="font-mono font-bold text-xs text-white hover:text-brand-400 transition-colors shrink-0"
                    >
                      {act.asset_tag}
                    </button>

                    <span className="text-slate-400 text-xs hidden sm:inline">•</span>

                    <span className="font-semibold text-xs text-slate-200 truncate">
                      {act.title}
                    </span>

                    <span className="text-slate-400 text-xs hidden lg:inline truncate">
                      — {act.why_it_matters}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 self-end md:self-auto">
                    {/* Status Dropdown with Server RBAC Enforcement */}
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] uppercase font-mono text-slate-400 font-semibold hidden sm:inline">Status:</span>
                      <select
                        value={currentStatus}
                        disabled={updatingId === act.action_id}
                        onChange={(e) => handleStatusChange(act, e.target.value)}
                        className={`text-xs font-mono font-semibold px-2.5 py-1 rounded-lg border bg-slate-950 transition-all ${getStatusColor(currentStatus)}`}
                      >
                        <option value="Open">Open</option>
                        <option value="Investigating">Investigating</option>
                        <option value="In Progress">In Progress</option>
                        <option value="Resolved">Resolved</option>
                        <option value="Closed">Closed</option>
                      </select>
                    </div>

                    {act.cmms_dispatched && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 shrink-0 flex items-center gap-1" title={`Dispatched to ${act.cmms_target_system}`}>
                        <CheckCircle2 className="w-2.5 h-2.5" />
                        <span className="hidden sm:inline">{act.cmms_reference_id}</span>
                      </span>
                    )}

                    <button
                      onClick={() => {
                        setDispatchModalAct(act);
                        setDispatchResult(null);
                        setDispatchNotes('');
                      }}
                      className="px-2.5 py-1.5 rounded-lg bg-indigo-500/15 hover:bg-indigo-500/25 text-indigo-300 border border-indigo-500/30 text-xs font-medium transition-all flex items-center gap-1 shrink-0"
                      title="Dispatch action to enterprise CMMS/ERP"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      <span className="hidden sm:inline">Dispatch CMMS</span>
                    </button>

                    <button
                      onClick={() => setExpandedId(isExpanded ? null : act.action_id)}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-all flex items-center gap-1"
                    >
                      <span>{isExpanded ? 'Collapse' : 'Review'}</span>
                      {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>

                {/* Expanded State */}
                {isExpanded && (
                  <div className="px-5 pb-5 pt-2 border-t border-slate-800/80 space-y-4 text-xs animate-in fade-in duration-150">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800">
                        <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block mb-1">
                          Why This Matters
                        </span>
                        <p className="text-slate-300 leading-relaxed">{act.why_it_matters}</p>
                      </div>

                      <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800">
                        <span className="text-[10px] font-mono uppercase tracking-wider text-brand-400 font-semibold block mb-1">
                          What Needs Action?
                        </span>
                        <p className="text-slate-200 font-medium leading-relaxed">{act.what_needs_action}</p>
                      </div>

                      <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 flex flex-col justify-between">
                        <div>
                          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block mb-1">
                            Evidence
                          </span>
                          <p className="text-slate-300 font-mono text-[11px]">{act.evidence}</p>
                        </div>
                        <div className="pt-2 flex items-center justify-between text-[11px] text-slate-400">
                          <span>Owner: <strong className="text-slate-200">{act.owner}</strong></span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-1">
                      <button
                        onClick={() => handleOpenEvidence(act)}
                        className="text-xs text-brand-400 hover:text-brand-300 font-medium flex items-center gap-1.5 transition-colors"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        <span>View Evidence</span>
                      </button>

                      <button
                        onClick={() => onSelectAsset(act.asset_tag)}
                        className="px-3.5 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white font-semibold text-xs flex items-center gap-1.5 transition-all shadow-md shadow-brand-500/20"
                      >
                        <span>Open Machine ({act.asset_tag})</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* RBAC PERMISSION DENIED MODAL (Separation of Duties Demonstration) */}
      {rbacErrorModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-150">
          <div className="bg-slate-900 border border-red-500/40 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-red-500/20 border border-red-500/30 flex items-center justify-center text-red-400">
                  <ShieldAlert className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-base">RBAC Authorization Denied (HTTP 403)</h3>
                  <p className="text-xs text-red-400 font-mono">Separation of Duties (SoD) Policy Violation</p>
                </div>
              </div>
              <button
                onClick={() => setRbacErrorModal(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
              <div className="flex justify-between text-slate-400">
                <span>Attempted Action:</span>
                <strong className="text-white font-mono">{rbacErrorModal.actionId}</strong>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Requested Status:</span>
                <span className="text-amber-400 font-bold font-mono">{rbacErrorModal.attemptedStatus}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Active Persona:</span>
                <span className="text-slate-200">{rbacErrorModal.userName}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Active Role:</span>
                <span className="text-brand-400 font-mono font-bold">{rbacErrorModal.userRole}</span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-red-950/20 border border-red-500/20 text-slate-300 text-xs leading-relaxed space-y-2">
              <p>
                <strong>Operational Boundary:</strong> Under the platform's Industrial Governance policy, operators assigned to <strong>{rbacErrorModal.userRole}</strong> cannot transition action items to <strong>'{rbacErrorModal.attemptedStatus}'</strong>.
              </p>
              <p className="text-[11px] text-slate-400">
                Resolving or closing critical overhaul actions requires <strong>Plant Manager</strong> or <strong>Administrator</strong> authorization. This unauthorized attempt has been logged to the system audit trail.
              </p>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setRbacErrorModal(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-all"
              >
                Acknowledge & Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CMMS DISPATCH MODAL */}
      {dispatchModalAct && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-150">
          <div className="bg-slate-900 border border-indigo-500/40 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                  <Layers className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-base">Enterprise CMMS / ERP Work Order Dispatch</h3>
                  <p className="text-xs text-indigo-400 font-mono">Clean Prototype Adapter Contract</p>
                </div>
              </div>
              <button
                onClick={() => setDispatchModalAct(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5 text-xs">
              <div className="flex justify-between text-slate-400">
                <span>Action:</span>
                <span className="text-white font-medium truncate max-w-[280px]">{dispatchModalAct.title}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Asset:</span>
                <strong className="text-brand-400 font-mono">{dispatchModalAct.asset_tag}</strong>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Severity:</span>
                <span className="text-amber-400 font-bold">{dispatchModalAct.severity}</span>
              </div>
            </div>

            {!dispatchResult ? (
              <form onSubmit={handleDispatchCmms} className="space-y-4">
                <div>
                  <label className="block text-[11px] font-mono uppercase text-slate-400 mb-1.5">
                    Target Enterprise System
                  </label>
                  <select
                    value={dispatchSystem}
                    onChange={(e) => setDispatchSystem(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
                  >
                    <option value="SAP_PM">SAP S/4HANA Plant Maintenance (PM) — Maintenance Notification</option>
                    <option value="IBM_MAXIMO">IBM Maximo Enterprise CMMS — Corrective Work Order</option>
                    <option value="ROCKWELL_MES">Rockwell FactoryTalk MES — Production Maintenance Hold</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-mono uppercase text-slate-400 mb-1.5">
                    Dispatch Notes / Work Scope
                  </label>
                  <textarea
                    rows={3}
                    value={dispatchNotes}
                    onChange={(e) => setDispatchNotes(e.target.value)}
                    placeholder="e.g. Schedule immediate drive-end bearing replacement per OEM Manual XYZ-200. Dispatched from IntelGraph Action Center."
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
                  />
                </div>

                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-[11px] text-slate-400">
                  <p>
                    <strong className="text-slate-300">Prototype Integration Contract:</strong> Dispatches payload through the configured enterprise adapter and logs an external work order reference ID to the audit trail.
                  </p>
                </div>

                <div className="flex items-center justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setDispatchModalAct(null)}
                    className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-all"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={dispatching}
                    className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-all shadow-lg shadow-indigo-600/30 disabled:opacity-50"
                  >
                    {dispatching ? <RotateCw className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                    <span>Dispatch Work Order</span>
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-4 animate-in fade-in duration-150">
                <div className="p-4 rounded-xl bg-emerald-950/30 border border-emerald-500/30 space-y-2 text-xs">
                  <div className="flex items-center gap-2 text-emerald-400 font-bold">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Successfully Dispatched to {dispatchResult.target_system}</span>
                  </div>
                  <div className="text-slate-300 font-mono text-[11px]">
                    External Reference ID: <strong className="text-white bg-slate-900 px-2 py-0.5 rounded border border-slate-800">{dispatchResult.external_reference_id}</strong>
                  </div>
                  <div className="text-slate-400 text-[11px]">
                    Timestamp: {dispatchResult.dispatched_at} | Dispatched By: {dispatchResult.dispatched_by}
                  </div>
                  <div className="text-slate-400 text-[11px] truncate">
                    Endpoint: {dispatchResult.endpoint_dispatched}
                  </div>
                </div>

                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={() => setDispatchModalAct(null)}
                    className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-all"
                  >
                    Close
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Evidence Drawer */}
      <EvidenceDrawer
        isOpen={evidenceDrawerOpen}
        onClose={() => setEvidenceDrawerOpen(false)}
        evidenceData={selectedEvidence}
      />
    </div>
  );
}
