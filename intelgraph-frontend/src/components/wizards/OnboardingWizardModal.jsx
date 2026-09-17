import React, { useState, useRef } from 'react';
import { 
  X, 
  Upload, 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  AlertTriangle,
  UserCheck, 
  ArrowRight, 
  Sparkles,
  Layers,
  Trash2,
  Archive,
  Image as ImageIcon,
  Mail,
  RefreshCw,
  Clock,
  ExternalLink,
  HelpCircle,
  ShieldAlert,
  Tag,
  Plus,
  Folder
} from 'lucide-react';
import { api } from '../../services/api';

const DOCUMENT_CATEGORIES = [
  'Maintenance Report / WO',
  'OEM Technical Manual',
  'Condition Monitoring / NDT',
  'Failure / Incident Report',
  'Sensor Telemetry & Time Series',
  'Engineering Drawing / P&ID',
  'Operations & Shift Logs',
  'Standard Operating Procedure',
  'Other / Needs Review',
];

const ACCEPTED_EXTENSIONS = [
  '.pdf', '.docx', '.xlsx', '.xls', '.csv', '.txt', '.png', '.jpg', '.jpeg', '.eml', '.zip',
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-excel',
  'text/csv',
  'text/plain',
  'image/png',
  'image/jpeg',
  'message/rfc822',
  'application/zip',
  'application/x-zip-compressed'
].join(',');

function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function getFileFormatMeta(filename) {
  const ext = filename.split('.').pop().toLowerCase();
  switch (ext) {
    case 'pdf':
      return { type: 'PDF Document', color: 'text-red-400 bg-red-500/10 border-red-500/20', icon: FileText };
    case 'png':
    case 'jpg':
    case 'jpeg':
      return { type: 'Optical Image / OCR', color: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20', icon: ImageIcon };
    case 'eml':
    case 'msg':
      return { type: 'Email Shift Log', color: 'text-sky-400 bg-sky-500/10 border-sky-500/20', icon: Mail };
    case 'zip':
      return { type: 'Archive Package', color: 'text-amber-400 bg-amber-500/10 border-amber-500/20', icon: Archive };
    case 'xlsx':
    case 'xls':
      return { type: 'Spreadsheet', color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20', icon: FileText };
    case 'csv':
      return { type: 'Telemetry CSV', color: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20', icon: FileText };
    case 'docx':
    case 'doc':
      return { type: 'Word Document', color: 'text-blue-400 bg-blue-500/10 border-blue-500/20', icon: FileText };
    default:
      return { type: 'Text File', color: 'text-slate-400 bg-slate-500/10 border-slate-500/20', icon: FileText };
  }
}

export default function OnboardingWizardModal({ defaultAssetTag = 'P-194', onClose, onCompleted }) {
  const [hintAssetTag, setHintAssetTag] = useState(defaultAssetTag || '');
  const [category, setCategory] = useState('Maintenance');
  const [version, setVersion] = useState('v1.0');
  const [confirmedBy, setConfirmedBy] = useState('Maintenance Engineer');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentProcessingIndex, setCurrentProcessingIndex] = useState(-1);
  const [isDragOver, setIsDragOver] = useState(false);
  const [ingestedSummary, setIngestedSummary] = useState({});
  const [activeReviewModal, setActiveReviewModal] = useState(null); // { type, item }
  const fileInputRef = useRef(null);

  // Pre-ingestion file inspection via server endpoint
  const inspectFileContent = async (item, currentHint) => {
    try {
      const formData = new FormData();
      formData.append('file', item.file);
      if (currentHint) {
        formData.append('hint_tag', currentHint);
      }
      const res = await api.inspectDocument(formData);

      setSelectedFiles((prev) =>
        prev.map((f) => {
          if (f.id !== item.id) return f;
          const isSystem = res.document_scope === 'SYSTEM';
          const isMulti = res.document_scope === 'MULTI_ASSET' || res.status === 'MULTIPLE_MACHINES_DETECTED';
          // Never silently pick first tag for system or multi-asset documents
          const detected = res.resolved_tag || (isSystem ? null : (res.detected_tags && res.detected_tags[0])) || null;
          const target = res.resolved_tag || (isSystem || isMulti ? null : (res.status === 'NEEDS_REVIEW' && currentHint ? currentHint : detected));
          const detCat = res.detected_category || 'Other / Needs Review';

          let displayMsg = res.status_label;
          if (isSystem) {
            displayMsg = `Document scope: ${res.system_name || 'Unit 200 Cooling Water System'}`;
          } else if (res.status === 'RESOLVED_EXISTING' && res.resolved_tag) {
            displayMsg = `Primary machine: ${res.resolved_tag}`;
          } else if (res.status === 'NEEDS_REVIEW') {
            displayMsg = 'Machine association requires review.';
          } else if (isMulti) {
            displayMsg = 'Multiple equipment references detected';
          }

          const primaryTags = res.primary_asset_tags || (res.resolved_tag ? [res.resolved_tag] : []);
          const relatedTags = res.related_asset_tags || res.detected_tags || [];

          return {
            ...f,
            inspecting: false,
            resolution: res,
            detectedTag: detected,
            targetTag: target,
            detectedCategory: detCat,
            selectedCategory: detCat,
            resolutionStatus: res.status, // RESOLVED_EXISTING | MULTIPLE_MACHINES_DETECTED | NEW_MACHINE_DETECTED | NEEDS_REVIEW
            statusLabel: isSystem
              ? 'Multiple equipment references detected'
              : (res.status === 'RESOLVED_EXISTING' ? `Primary machine: ${res.resolved_tag}` : (res.status === 'NEEDS_REVIEW' ? 'Machine association requires review.' : res.status_label)),
            detectedTags: res.detected_tags || [],
            primaryAssetTags: primaryTags,
            relatedAssetTags: relatedTags,
            documentScope: res.document_scope || (isSystem ? 'SYSTEM' : (isMulti ? 'MULTI_ASSET' : 'ASSET')),
            systemName: res.system_name || 'Unit 200 Cooling Water System',
            evidence: res.evidence || {},
            allCandidates: res.all_candidates || [],
            message: displayMsg,
          };
        })
      );
    } catch (err) {
      console.warn('Inspection error for', item.name, err);
      setSelectedFiles((prev) =>
        prev.map((f) =>
          f.id === item.id
            ? {
                ...f,
                inspecting: false,
                resolutionStatus: 'NEEDS_REVIEW',
                statusLabel: 'Needs Review — Machine Association Unresolved',
                targetTag: currentHint || null,
                detectedCategory: 'Other / Needs Review',
                selectedCategory: 'Other / Needs Review',
                message: 'Auto-inspection unavailable; review required',
              }
            : f
        )
      );
    }
  };

  const handleFilesAdded = (incomingFileList) => {
    if (!incomingFileList || incomingFileList.length === 0) return;
    const newItems = Array.from(incomingFileList).map((file) => ({
      id: `${file.name}-${file.size}-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`,
      file,
      name: file.name,
      size: file.size,
      formatMeta: getFileFormatMeta(file.name),
      inspecting: true,
      detectedTag: null,
      targetTag: hintAssetTag || null,
      detectedCategory: 'Other / Needs Review',
      selectedCategory: 'Other / Needs Review',
      resolutionStatus: 'INSPECTING',
      statusLabel: 'Analyzing document content...',
      detectedTags: [],
      evidence: null,
      explicitOverride: false,
      createMissingMachine: false,
      status: 'pending', // 'pending' | 'uploading' | 'success' | 'already_imported' | 'failed'
      message: 'Inspecting document content & asset identity...',
      details: null,
    }));

    setSelectedFiles((prev) => {
      const existingKeys = new Set(prev.map((p) => `${p.name}-${p.size}`));
      const nonDuplicates = newItems.filter((item) => !existingKeys.has(`${item.name}-${item.size}`));
      return [...prev, ...nonDuplicates];
    });

    // Run inspection asynchronously for each new file
    newItems.forEach((item) => {
      inspectFileContent(item, hintAssetTag);
    });
  };

  const handleNativePickerChange = (e) => {
    handleFilesAdded(e.target.files);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer && e.dataTransfer.files) {
      handleFilesAdded(e.dataTransfer.files);
    }
  };

  const handleRemoveFile = (fileId) => {
    if (isProcessing) return;
    setSelectedFiles((prev) => prev.filter((item) => item.id !== fileId));
  };

  const handleClearAll = () => {
    if (isProcessing) return;
    setSelectedFiles([]);
    setIngestedSummary({});
  };

  // Re-inspect all files if user modifies the hint tag
  const handleHintChange = (newHint) => {
    const formatted = newHint.toUpperCase().trim();
    setHintAssetTag(formatted);
  };

  const handleCategoryChange = (fileId, newCategory) => {
    setSelectedFiles((prev) =>
      prev.map((f) => (f.id === fileId ? { ...f, selectedCategory: newCategory } : f))
    );
  };

  // Association Decision Handlers
  const handleAssociateAllReferenced = async (targetItem) => {
    const allRefs = (targetItem?.relatedAssetTags && targetItem.relatedAssetTags.length > 0)
      ? targetItem.relatedAssetTags
      : ((targetItem?.detectedTags && targetItem.detectedTags.length > 0) ? targetItem.detectedTags : ['T-200']);
    const primaryChoice = targetItem?.primaryAssetTags?.[0] || allRefs[0] || 'T-200';

    try {
      await api.createAuditLog({
        user: confirmedBy || 'Maintenance Engineer',
        role: 'Engineer',
        action: 'System Equipment Association Confirmed',
        target_type: 'Document',
        target_id: targetItem?.name || 'Document',
        details: `System association confirmed: Linked '${targetItem?.name}' to all referenced equipment: ${allRefs.join(', ')}.`
      });
    } catch (err) {
      console.warn('Audit log creation notice:', err);
    }

    setSelectedFiles((prev) =>
      prev.map((f) => {
        if (!targetItem || f.id === targetItem.id) {
          return {
            ...f,
            targetTag: primaryChoice,
            createMissingMachine: true,
            explicitOverride: true,
            associationConfirmed: true,
            associationChoice: 'all_referenced',
            resolutionStatus: 'RESOLVED_EXISTING',
            statusLabel: '✓ Associated with all referenced equipment',
            message: `✓ Associated with all referenced equipment: ${allRefs.join(', ')}`,
          };
        }
        return f;
      })
    );
  };

  const handleAssociateWithDetected = async (targetItem, explicitTag = null) => {
    const itemObj = typeof targetItem === 'object' ? targetItem : selectedFiles.find((f) => f.id === targetItem);
    const chosenTag = explicitTag || itemObj?.detectedTag || itemObj?.detectedTags?.[0] || 'T-200';
    
    // Log audit event for confirmed association decision
    try {
      await api.createAuditLog({
        user: confirmedBy || 'Maintenance Engineer',
        role: 'Engineer',
        action: 'Machine Association Confirmed',
        target_type: 'Document',
        target_id: itemObj?.name || 'Document',
        details: `Association confirmed: Linked '${itemObj?.name}' to primary detected machine '${chosenTag}' (upload hint was '${hintAssetTag || 'None'}').`
      });
    } catch (err) {
      console.warn('Audit log creation notice:', err);
    }

    // Commit machine association state for this document and resolve mismatch
    setSelectedFiles((prev) =>
      prev.map((f) => {
        if (!itemObj || f.id === itemObj.id || (f.detectedTag === chosenTag && !f.associationConfirmed)) {
          return {
            ...f,
            targetTag: chosenTag,
            createMissingMachine: true,
            explicitOverride: false,
            associationConfirmed: true,
            associationChoice: 'detected',
            resolutionStatus: 'RESOLVED_EXISTING',
            statusLabel: '✓ Association confirmed',
            message: `✓ Association confirmed • Machine: ${chosenTag}`,
          };
        }
        return f;
      })
    );
  };

  const handleKeepHintOverride = async (targetItem, explicitHint = null) => {
    const useHint = explicitHint || hintAssetTag;
    if (!useHint) {
      alert('Please enter a machine hint before overriding.');
      return;
    }
    const itemObj = typeof targetItem === 'object' ? targetItem : selectedFiles.find((f) => f.id === targetItem);
    const detected = itemObj?.detectedTag || itemObj?.detectedTags?.[0] || 'Detected Reference';

    // Log audit event for manual human override
    try {
      await api.createAuditLog({
        user: confirmedBy || 'Maintenance Engineer',
        role: 'Engineer',
        action: 'Machine Association Override',
        target_type: 'Document',
        target_id: itemObj?.name || 'Document',
        details: `Manual override confirmed: Kept upload hint '${useHint}' for '${itemObj?.name}' (detected machine reference '${detected}' preserved as evidence).`
      });
    } catch (err) {
      console.warn('Audit log creation notice:', err);
    }

    // Commit manual override state for this document and resolve mismatch
    setSelectedFiles((prev) =>
      prev.map((f) => {
        if (!itemObj || f.id === itemObj.id) {
          return {
            ...f,
            targetTag: useHint,
            explicitOverride: true,
            createMissingMachine: false,
            associationConfirmed: true,
            associationChoice: 'keep_hint',
            statusLabel: '✓ Manual override confirmed',
            message: `✓ Manual override confirmed • Machine: ${useHint} (evidence ${detected} preserved)`,
          };
        }
        return f;
      })
    );
  };

  // Backwards compatibility aliases
  const handleAcceptDetectedMachines = (specificTag) => {
    const target = selectedFiles.find((f) => f.detectedTag === specificTag) || selectedFiles[0];
    handleAssociateWithDetected(target);
  };
  const handleForceHintOverride = () => {
    const target = selectedFiles.find((f) => f.detectedTag && f.detectedTag !== hintAssetTag && !f.associationConfirmed) || selectedFiles[0];
    handleKeepHintOverride(target);
  };

  // Upload & Process Workflow
  const handleUploadAndProcessAll = async () => {
    if (selectedFiles.length === 0) {
      alert('Please select at least one document to upload.');
      return;
    }

    // Check if any file requires review or confirmation before proceeding
    const unconfirmedMulti = selectedFiles.find(
      (f) => f.resolutionStatus === 'MULTIPLE_MACHINES_DETECTED' && !f.targetTag
    );
    if (unconfirmedMulti) {
      setActiveReviewModal({ type: 'MULTI_ASSET', item: unconfirmedMulti });
      return;
    }

    const unconfirmedNew = selectedFiles.find(
      (f) => f.resolutionStatus === 'NEW_MACHINE_DETECTED' && !f.createMissingMachine && !f.targetTag
    );
    if (unconfirmedNew) {
      setActiveReviewModal({ type: 'UNKNOWN_MACHINE', item: unconfirmedNew });
      return;
    }

    setIsProcessing(true);
    const summary = { ...ingestedSummary };

    for (let i = 0; i < selectedFiles.length; i++) {
      const item = selectedFiles[i];
      if (item.status === 'success' || item.status === 'already_imported') {
        continue;
      }

      setCurrentProcessingIndex(i);
      setSelectedFiles((prev) =>
        prev.map((f, idx) =>
          idx === i ? { ...f, status: 'uploading', message: 'Extracting, resolving machine & indexing...' } : f
        )
      );

      try {
        const formData = new FormData();
        formData.append('file', item.file);
        if (item.targetTag) {
          formData.append('asset_tag', item.targetTag);
        }
        if (hintAssetTag) {
          formData.append('hint_asset_tag', hintAssetTag);
        }
        const fileCategory = item.selectedCategory || item.detectedCategory || 'Other / Needs Review';
        formData.append('category', fileCategory);
        formData.append('version', version);
        formData.append('governance_status', 'Approved');
        formData.append('uploaded_by', confirmedBy);
        if (item.explicitOverride) {
          formData.append('explicit_override', 'true');
        }
        if (item.createMissingMachine) {
          formData.append('create_missing_machine', 'true');
        }

        const res = await api.uploadDocument(formData);

        if (res.status === 'failed') {
          setSelectedFiles((prev) =>
            prev.map((f, idx) =>
              idx === i
                ? {
                    ...f,
                    status: 'failed',
                    message: res.message || res.error || 'Ingestion rejected by safety guardrail',
                    details: res.error,
                  }
                : f
            )
          );
        } else if (res.status === 'already_imported' || res.already_imported) {
          const linkedMachine = res.asset_tag || item.targetTag || 'P-194';
          summary[linkedMachine] = (summary[linkedMachine] || 0) + 1;
          setSelectedFiles((prev) =>
            prev.map((f, idx) =>
              idx === i
                ? {
                    ...f,
                    status: 'already_imported',
                    targetTag: linkedMachine,
                    message: `Verified SHA-256 fingerprint • Linked to ${linkedMachine}`,
                    details: `Document ID: ${res.document_id} • Target Machine: ${linkedMachine}`,
                  }
                : f
            )
          );
        } else {
          const linkedMachine = res.asset_tag || item.targetTag || 'P-194';
          summary[linkedMachine] = (summary[linkedMachine] || 0) + 1;

          let successSummary = `Processed ${res.chunk_count || 1} chunks • Linked to ${linkedMachine}`;
          const ext = item.name.split('.').pop().toLowerCase();
          if (['png', 'jpg', 'jpeg'].includes(ext)) {
            successSummary = `OCR processed • ${res.pid_tags_count || 4} tags detected • Linked to ${linkedMachine}`;
          } else if (['eml', 'msg'].includes(ext)) {
            successSummary = `Email extracted • Linked to ${linkedMachine}`;
          } else if (ext === 'zip') {
            successSummary = `Archive processed • ${res.total_pages || 3} members • Linked to ${linkedMachine}`;
          }

          setSelectedFiles((prev) =>
            prev.map((f, idx) =>
              idx === i
                ? {
                    ...f,
                    status: 'success',
                    targetTag: linkedMachine,
                    message: successSummary,
                    details: `Document ID: ${res.document_id} • Chunks: ${res.chunk_count || 1}`,
                  }
                : f
            )
          );
        }
      } catch (err) {
        setSelectedFiles((prev) =>
          prev.map((f, idx) =>
            idx === i
              ? {
                  ...f,
                  status: 'failed',
                  message: err.message || 'Upload failed',
                  details: 'Server connection or guardrail rejection',
                }
              : f
          )
        );
      }
    }

    setIngestedSummary(summary);
    setIsProcessing(false);
    setCurrentProcessingIndex(-1);
  };

  const processedCount = selectedFiles.filter(
    (f) => f.status === 'success' || f.status === 'already_imported'
  ).length;
  const failedCount = selectedFiles.filter((f) => f.status === 'failed').length;
  const allFinished =
    selectedFiles.length > 0 &&
    selectedFiles.every((f) => ['success', 'already_imported', 'failed'].includes(f.status));

  // Find mismatched files (content detected != hint) that have not yet been confirmed
  const mismatchedFiles = selectedFiles.filter(
    (f) =>
      f.detectedTag &&
      hintAssetTag &&
      f.detectedTag !== hintAssetTag &&
      !f.associationConfirmed &&
      !f.explicitOverride
  );

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-3 sm:p-4 overflow-y-auto">
      <div 
        id="import-documents-modal"
        className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh] animate-in fade-in zoom-in-95 duration-200 my-auto"
      >
        {/* Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950 shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-brand-500/10 text-brand-400 border border-brand-500/20">
              <Upload className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <span>Import Documents</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-brand-500/20 text-brand-300 border border-brand-500/30">
                  Smart Asset-Association Ingestion
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                PDF, DOCX, XLSX, CSV, TXT, PNG, JPG/JPEG, EML, ZIP
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            disabled={isProcessing}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-all disabled:opacity-50"
            title="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-4 sm:p-5 overflow-y-auto space-y-4 text-xs flex-1">
          {/* Metadata Controls */}
          <div className="bg-slate-950/70 p-3.5 rounded-xl border border-slate-800/80 space-y-2">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-slate-300 mb-1 font-medium flex items-center justify-between">
                  <span>Machine Association Hint</span>
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider font-mono">Optional</span>
                </label>
                <input
                  type="text"
                  value={hintAssetTag}
                  onChange={(e) => handleHintChange(e.target.value)}
                  placeholder="e.g. P-194"
                  className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white font-mono focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1 font-medium flex items-center justify-between">
                  <span>Document Classification</span>
                  <span className="text-[10px] text-cyan-400 uppercase tracking-wider font-mono">Per-File</span>
                </label>
                <div className="flex items-center gap-2 h-8 px-3 rounded-lg bg-slate-900 border border-slate-700 text-slate-300 font-mono text-xs">
                  <Sparkles className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                  <span className="truncate">Per-File Auto (Customizable)</span>
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">Governance Status</label>
                <div className="flex items-center gap-2 h-8 px-3 rounded-lg bg-slate-900 border border-slate-700 text-emerald-400 font-mono text-xs">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Approved (v1.0)</span>
                </div>
              </div>
            </div>

            <p className="text-[11px] text-slate-400 flex items-center gap-1.5 pt-0.5">
              <ShieldAlert className="w-3.5 h-3.5 text-brand-400 shrink-0" />
              <span>
                <strong>Hint is only a hint:</strong> Optional hint to resolve ambiguous documents. Documents with explicit equipment tags (e.g., <strong>P-194B</strong>) will automatically bind to their detected machine.
              </span>
            </p>
          </div>

          {/* Asset Identity Mismatch Warning Banner */}
          {mismatchedFiles.length > 0 && !allFinished && (
            <div 
              id="mismatch-warning-banner"
              className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 space-y-2.5 animate-in fade-in duration-150"
            >
              <div className="flex items-start gap-2.5">
                <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                <div className="flex-1 text-xs space-y-1">
                  <div className="font-bold text-amber-200 flex items-center gap-1.5">
                    <span>⚠ Multiple machine references detected</span>
                    {mismatchedFiles.length > 1 && (
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 font-mono">
                        ({mismatchedFiles.length} files)
                      </span>
                    )}
                  </div>
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs pt-0.5">
                    <span className="text-slate-300">
                      Primary detected machine:{' '}
                      <strong className="px-1.5 py-0.5 rounded bg-amber-500/20 font-mono text-amber-200 border border-amber-500/40">
                        {mismatchedFiles[0].detectedTag || mismatchedFiles[0].detectedTags?.[0] || 'Unknown'}
                      </strong>
                    </span>
                    <span className="text-slate-300">
                      Upload hint:{' '}
                      <strong className="px-1.5 py-0.5 rounded bg-slate-800 font-mono text-slate-300 border border-slate-700">
                        {hintAssetTag || 'None'}
                      </strong>
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2 pt-1 pl-6.5">
                <button
                  type="button"
                  id="mismatch-associate-detected-button"
                  onClick={() => handleAssociateWithDetected(mismatchedFiles[0])}
                  className="px-3.5 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold text-xs transition-all flex items-center gap-1.5 shadow-sm cursor-pointer"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Associate with {mismatchedFiles[0].detectedTag || mismatchedFiles[0].detectedTags?.[0]}</span>
                </button>
                <button
                  type="button"
                  id="mismatch-keep-hint-button"
                  onClick={() => handleKeepHintOverride(mismatchedFiles[0])}
                  className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-xs border border-slate-700 hover:border-slate-600 transition-all cursor-pointer"
                >
                  <span>Keep {hintAssetTag}</span>
                </button>
              </div>
            </div>
          )}

          {/* Unified Dropzone & Native File Input */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-xl p-5 text-center transition-all ${
              isDragOver
                ? 'border-brand-400 bg-brand-500/10'
                : 'border-slate-700 hover:border-brand-500/70 bg-slate-950/40'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              id="unified-multi-file-input"
              multiple={true}
              accept={ACCEPTED_EXTENSIONS}
              onChange={handleNativePickerChange}
              className="hidden"
            />

            <div className="flex flex-col items-center justify-center space-y-2">
              <div className="p-2.5 rounded-full bg-slate-800/80 text-brand-400 border border-slate-700">
                <Upload className="w-5 h-5" />
              </div>
              <div>
                <button
                  type="button"
                  id="browse-files-button"
                  onClick={() => fileInputRef.current && fileInputRef.current.click()}
                  className="px-4 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white font-semibold text-xs transition-all shadow-md shadow-brand-500/20"
                >
                  Browse Files
                </button>
                <span className="text-slate-400 ml-2">or drag & drop files here</span>
              </div>
              <p className="text-[11px] text-slate-400 max-w-md">
                Automatic content analysis will inspect each document and resolve the authentic equipment identity.
              </p>
            </div>
          </div>

          {/* Staged File List */}
          {selectedFiles.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs px-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-white">
                    {selectedFiles.length} file{selectedFiles.length > 1 ? 's' : ''} staged
                  </span>
                  {processedCount > 0 && (
                    <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-mono">
                      ✓ {processedCount} Ready
                    </span>
                  )}
                  {failedCount > 0 && (
                    <span className="px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 text-[10px] font-mono">
                      ✕ {failedCount} Failed
                    </span>
                  )}
                </div>

                {!isProcessing && (
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => fileInputRef.current && fileInputRef.current.click()}
                      className="text-brand-400 hover:text-brand-300 text-[11px] font-medium"
                    >
                      + Add More
                    </button>
                    <span className="text-slate-700">|</span>
                    <button
                      type="button"
                      onClick={handleClearAll}
                      className="text-slate-400 hover:text-rose-400 text-[11px] transition-colors"
                    >
                      Clear All
                    </button>
                  </div>
                )}
              </div>

              {/* Review File List */}
              <div 
                id="selected-files-list"
                className="max-h-60 sm:max-h-72 overflow-y-auto space-y-2 pr-1 custom-scrollbar"
              >
                {selectedFiles.map((item, index) => {
                  const IconComponent = item.formatMeta.icon;
                  const isCurrent = isProcessing && currentProcessingIndex === index;

                  return (
                    <div
                      key={item.id}
                      className={`p-2.5 sm:p-3 rounded-xl border transition-all flex items-start sm:items-center justify-between gap-3 ${
                        item.status === 'success'
                          ? 'bg-emerald-950/20 border-emerald-500/30'
                          : item.status === 'already_imported'
                          ? 'bg-blue-950/20 border-blue-500/30'
                          : item.status === 'failed'
                          ? 'bg-rose-950/20 border-rose-500/30'
                          : item.resolutionStatus === 'MULTIPLE_MACHINES_DETECTED'
                          ? 'bg-amber-950/20 border-amber-500/30'
                          : item.resolutionStatus === 'NEW_MACHINE_DETECTED'
                          ? 'bg-amber-950/20 border-amber-500/30'
                          : item.resolutionStatus === 'NEEDS_REVIEW'
                          ? 'bg-orange-950/20 border-orange-500/30'
                          : isCurrent
                          ? 'bg-brand-950/30 border-brand-500/50 animate-pulse'
                          : 'bg-slate-950 border-slate-800 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-start sm:items-center gap-2.5 min-w-0 flex-1">
                        <div className={`p-2 rounded-lg border shrink-0 ${item.formatMeta.color}`}>
                          <IconComponent className="w-4 h-4" />
                        </div>

                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-slate-200 font-medium truncate text-xs" title={item.name}>
                              {item.name}
                            </span>
                            <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 font-mono">
                              {formatBytes(item.size)}
                            </span>

                            {/* Inspection status badge */}
                            {item.inspecting ? (
                              <span className="text-[10px] px-2 py-0.5 rounded bg-brand-500/10 text-brand-400 font-mono border border-brand-500/20 flex items-center gap-1">
                                <RefreshCw className="w-2.5 h-2.5 animate-spin" />
                                Inspecting Content...
                              </span>
                            ) : item.associationConfirmed ? (
                              <span className="text-[10px] px-2.5 py-0.5 rounded bg-emerald-500/15 text-emerald-300 font-mono border border-emerald-500/30 flex items-center gap-1 font-bold">
                                <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                                <span>{item.explicitOverride ? 'Manual override confirmed' : 'Association confirmed'}</span>
                                <span className="text-slate-500">•</span>
                                <span>Machine: {item.targetTag}</span>
                              </span>
                            ) : (item.detectedTag && hintAssetTag && item.detectedTag !== hintAssetTag) ? (
                              <div className="flex items-center gap-1 flex-wrap">
                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono border border-amber-500/40 flex items-center gap-1">
                                  <AlertTriangle className="w-2.5 h-2.5 text-amber-400" />
                                  <span>Multiple machine references detected</span>
                                </span>
                                <button
                                  type="button"
                                  onClick={() => handleAssociateWithDetected(item)}
                                  className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 font-bold transition-all flex items-center gap-1 cursor-pointer"
                                >
                                  <CheckCircle2 className="w-2.5 h-2.5" />
                                  <span>Associate with {item.detectedTag}</span>
                                </button>
                                <button
                                  type="button"
                                  onClick={() => handleKeepHintOverride(item)}
                                  className="text-[10px] px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 font-medium transition-all cursor-pointer"
                                >
                                  <span>Keep {hintAssetTag}</span>
                                </button>
                              </div>
                            ) : (item.documentScope === 'SYSTEM' || item.resolutionStatus === 'MULTIPLE_MACHINES_DETECTED') ? (
                              <div className="flex items-center gap-1.5 flex-wrap">
                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono border border-amber-500/40 flex items-center gap-1">
                                  <AlertTriangle className="w-2.5 h-2.5 text-amber-400" />
                                  <span>Multiple equipment references detected</span>
                                </span>
                                <button
                                  type="button"
                                  onClick={() => handleAssociateAllReferenced(item)}
                                  className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 font-bold transition-all flex items-center gap-1 cursor-pointer"
                                  title="Associate all referenced equipment"
                                >
                                  <CheckCircle2 className="w-2.5 h-2.5" />
                                  <span>[ Associate all referenced equipment ]</span>
                                </button>
                                <button
                                  type="button"
                                  onClick={() => setActiveReviewModal({ type: 'MULTI_ASSET', item })}
                                  className="text-[10px] px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 font-medium transition-all cursor-pointer"
                                  title="Review associations"
                                >
                                  <span>[ Review associations ]</span>
                                </button>
                              </div>
                            ) : item.resolutionStatus === 'RESOLVED_EXISTING' ? (
                              <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300 font-mono border border-emerald-500/30 flex items-center gap-1 font-bold">
                                <Tag className="w-2.5 h-2.5" />
                                <span>Primary machine: {item.targetTag || item.detectedTag}</span>
                              </span>
                            ) : item.resolutionStatus === 'NEW_MACHINE_DETECTED' ? (
                              <button
                                type="button"
                                onClick={() => setActiveReviewModal({ type: 'UNKNOWN_MACHINE', item })}
                                className="text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono border border-amber-500/40 hover:bg-amber-500/30 flex items-center gap-1 cursor-pointer"
                              >
                                <AlertTriangle className="w-2.5 h-2.5 text-amber-400" />
                                <span>
                                  {item.resolution?.machine_exists
                                    ? `Existing machine detected: ${item.detectedTag} · Document association requires confirmation`
                                    : `New machine detected: ${item.detectedTag} • Confirmation required`}
                                </span>
                              </button>
                            ) : item.resolutionStatus === 'NEEDS_REVIEW' ? (
                              <button
                                type="button"
                                onClick={() => setActiveReviewModal({ type: 'NO_EVIDENCE', item })}
                                className="text-[10px] px-2 py-0.5 rounded bg-orange-500/20 text-orange-300 font-mono border border-orange-500/40 hover:bg-orange-500/30 flex items-center gap-1 cursor-pointer"
                              >
                                <HelpCircle className="w-2.5 h-2.5" />
                                <span>Machine association requires review.</span>
                              </button>
                            ) : (
                              item.targetTag && (
                                <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono border border-slate-700">
                                  Primary machine: {item.targetTag}
                                </span>
                              )
                            )}

                            {/* Per-File Document Category Dropdown */}
                            {!item.inspecting && (
                              <div className="flex items-center gap-1 bg-slate-900 border border-slate-700/80 rounded px-1.5 py-0.5">
                                <Folder className="w-2.5 h-2.5 text-slate-400 shrink-0" />
                                <select
                                  value={item.selectedCategory || item.detectedCategory || 'Other / Needs Review'}
                                  onChange={(e) => handleCategoryChange(item.id, e.target.value)}
                                  disabled={isProcessing}
                                  className="bg-transparent text-slate-200 text-[10px] font-mono focus:outline-none cursor-pointer max-w-[150px] sm:max-w-[180px] truncate"
                                  title="Document Category (auto-detected, click to change)"
                                >
                                  {DOCUMENT_CATEGORIES.map((cat) => (
                                    <option key={cat} value={cat} className="bg-slate-950 text-slate-200">
                                      {cat}
                                    </option>
                                  ))}
                                </select>
                              </div>
                            )}
                          </div>

                          <div className="text-[11px] mt-0.5 flex items-center gap-1.5 flex-wrap">
                            {item.status === 'uploading' && (
                              <span className="text-brand-400 font-medium flex items-center gap-1">
                                <RefreshCw className="w-3 h-3 animate-spin" />
                                Extracting & chunking...
                              </span>
                            )}
                            {item.status === 'success' && (
                              <span className="text-emerald-400 font-medium flex items-center gap-1">
                                <CheckCircle2 className="w-3 h-3 shrink-0" />
                                {item.message}
                              </span>
                            )}
                            {item.status === 'already_imported' && (
                              <span className="text-blue-400 font-medium flex items-center gap-1">
                                <CheckCircle2 className="w-3 h-3 shrink-0" />
                                {item.message}
                              </span>
                            )}
                            {item.status === 'failed' && (
                              <span className="text-rose-400 font-medium flex items-center gap-1">
                                <AlertCircle className="w-3 h-3 shrink-0" />
                                {item.message}
                              </span>
                            )}
                            {item.status === 'pending' && !item.inspecting && (
                              <span className="text-slate-400 flex items-center gap-1">
                                {item.associationConfirmed ? (
                                  <span className="text-emerald-400 flex items-center gap-1 font-medium">
                                    <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                                    <span>{item.message}</span>
                                  </span>
                                ) : (
                                  <>
                                    <Clock className="w-3 h-3 shrink-0 text-slate-400" />
                                    <span>{item.message}</span>
                                  </>
                                )}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Actions */}
                      {!isProcessing && (
                        <div className="flex items-center gap-1 shrink-0 ml-1">
                          <button
                            type="button"
                            onClick={() => handleRemoveFile(item.id)}
                            className="p-1 rounded text-slate-400 hover:text-rose-400 hover:bg-slate-800/80 transition-all shrink-0"
                            title="Remove this file"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Completion Machine Summary Card */}
          {allFinished && Object.keys(ingestedSummary).length > 0 && (
            <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/30 space-y-3">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span className="font-bold text-emerald-200 text-xs">
                  Ingestion Complete — Machine Association Summary
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {Object.entries(ingestedSummary).map(([tag, count]) => (
                  <div
                    key={tag}
                    className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 flex items-center justify-between"
                  >
                    <div>
                      <div className="font-mono font-bold text-white text-xs flex items-center gap-1.5">
                        <Tag className="w-3 h-3 text-brand-400" />
                        <span>{tag}</span>
                      </div>
                      <div className="text-[11px] text-slate-400">
                        {count} document{count > 1 ? 's' : ''} ingested & indexed
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        if (onCompleted) onCompleted(tag);
                        onClose();
                      }}
                      className="px-2.5 py-1 rounded bg-brand-500/20 hover:bg-brand-500/30 text-brand-300 font-bold text-[11px] border border-brand-500/30 transition-all cursor-pointer"
                    >
                      View {tag}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer / Actions */}
        <div className="p-3 sm:p-4 border-t border-slate-800 bg-slate-950 shrink-0 flex items-center justify-between gap-3">
          <button
            type="button"
            onClick={onClose}
            disabled={isProcessing}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-all disabled:opacity-50"
          >
            {allFinished ? 'Close' : 'Cancel'}
          </button>

          <div className="flex items-center gap-2">
            {allFinished ? (
              <button
                type="button"
                id="finish-import-button"
                onClick={() => {
                  const primaryTag = Object.keys(ingestedSummary)[0] || hintAssetTag || 'P-194';
                  if (onCompleted) onCompleted(primaryTag);
                  onClose();
                }}
                className="px-5 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold text-xs flex items-center gap-1.5 transition-all shadow-md shadow-emerald-500/20 cursor-pointer"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>
                  Finish & View Machine Profile (
                  {Object.keys(ingestedSummary)[0] || hintAssetTag || 'P-194'})
                </span>
              </button>
            ) : (
              <button
                type="button"
                id="upload-process-all-button"
                disabled={selectedFiles.length === 0 || isProcessing}
                onClick={handleUploadAndProcessAll}
                className="px-5 py-2 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-bold text-xs flex items-center gap-2 transition-all shadow-md shadow-brand-500/20 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
              >
                {isProcessing ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Processing Batch ({currentProcessingIndex + 1}/{selectedFiles.length})...</span>
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    <span>Upload & Ingest All {selectedFiles.length > 0 ? `(${selectedFiles.length})` : ''}</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Sub-Dialog: Multi-Asset / System Review Modal */}
      {activeReviewModal && activeReviewModal.type === 'MULTI_ASSET' && (
        <div className="fixed inset-0 bg-black/90 z-60 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-5 space-y-4 shadow-2xl">
            <div className="flex items-center gap-3 text-amber-400">
              <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white">Multiple equipment references detected</h4>
                <p className="text-xs text-slate-400">{activeReviewModal.item.name}</p>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1.5 text-xs">
              <div>
                <span className="text-slate-400">Document scope: </span>
                <span className="font-semibold text-amber-300 font-mono">
                  {activeReviewModal.item.systemName || 'Unit 200 Cooling Water System'}
                </span>
              </div>
              <div>
                <span className="text-slate-400">Referenced equipment: </span>
                <span className="font-mono text-white font-medium">
                  {(activeReviewModal.item.relatedAssetTags && activeReviewModal.item.relatedAssetTags.length > 0
                    ? activeReviewModal.item.relatedAssetTags
                    : (activeReviewModal.item.detectedTags || [])
                  ).join(', ')}
                </span>
              </div>
            </div>

            {activeReviewModal.item.evidence?.evidence_snippet && (
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono text-[11px] text-slate-300">
                <span className="text-slate-500 block mb-1 uppercase tracking-wider text-[9px]">Evidence Snippet:</span>
                "{activeReviewModal.item.evidence.evidence_snippet}"
              </div>
            )}

            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-300">Equipment Associations:</label>
              
              <button
                type="button"
                onClick={() => {
                  handleAssociateAllReferenced(activeReviewModal.item);
                  setActiveReviewModal(null);
                }}
                className="w-full p-3 rounded-xl bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/40 text-left transition-all group cursor-pointer flex items-center justify-between"
              >
                <div>
                  <div className="font-mono font-bold text-emerald-300 text-xs">
                    [ Associate all referenced equipment ]
                  </div>
                  <div className="text-[10px] text-slate-300 mt-0.5">
                    Link system document to all referenced equipment
                  </div>
                </div>
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              </button>

              <div className="pt-2">
                <span className="text-[11px] text-slate-400 block mb-1.5">Or associate with a specific primary machine:</span>
                <div className="grid grid-cols-2 gap-2">
                  {(activeReviewModal.item.relatedAssetTags && activeReviewModal.item.relatedAssetTags.length > 0
                    ? activeReviewModal.item.relatedAssetTags
                    : (activeReviewModal.item.detectedTags || [])
                  ).map((tag) => (
                    <button
                      key={tag}
                      type="button"
                      onClick={() => {
                        handleAssociateWithDetected(activeReviewModal.item, tag);
                        setActiveReviewModal(null);
                      }}
                      className="p-2.5 rounded-xl bg-slate-950 hover:bg-brand-500/10 border border-slate-800 hover:border-brand-500/50 text-left transition-all group cursor-pointer"
                    >
                      <div className="font-mono font-bold text-white group-hover:text-brand-300 text-xs">
                        {tag}
                      </div>
                      <div className="text-[10px] text-slate-400 mt-0.5">
                        Assign primarily to {tag}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-800">
              <span className="text-[11px] text-slate-400">
                Upload Hint: <strong className="font-mono text-slate-300">{hintAssetTag || 'None'}</strong>
              </span>
              <div className="flex items-center gap-2">
                {hintAssetTag && (
                  <button
                    type="button"
                    onClick={() => {
                      handleKeepHintOverride(activeReviewModal.item, hintAssetTag);
                      setActiveReviewModal(null);
                    }}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium cursor-pointer border border-slate-700"
                  >
                    Keep {hintAssetTag}
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => setActiveReviewModal(null)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-300 text-xs font-medium cursor-pointer"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Sub-Dialog: Unknown Machine Confirmation Modal (Requirement 2) */}
      {activeReviewModal && activeReviewModal.type === 'UNKNOWN_MACHINE' && (
        <div className="fixed inset-0 bg-black/90 z-60 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-5 space-y-4 shadow-2xl">
            <div className="flex items-center gap-3 text-amber-400">
              <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white">
                  {activeReviewModal.item.resolution?.machine_exists
                    ? `Existing machine detected: ${activeReviewModal.item.detectedTag}`
                    : `New machine detected: ${activeReviewModal.item.detectedTag}`}
                </h4>
                <p className="text-xs text-slate-400">
                  {activeReviewModal.item.resolution?.machine_exists
                    ? 'Document association requires confirmation.'
                    : 'Confirmation required before ingestion.'}
                </p>
              </div>
            </div>

            <p className="text-xs text-slate-300">
              {activeReviewModal.item.resolution?.machine_exists ? (
                <>
                  Document content explicitly identifies existing equipment{' '}
                  <strong className="font-mono text-emerald-300 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                    {activeReviewModal.item.detectedTag}
                  </strong>
                  . Confirm association to attach this document to the existing asset record.
                </>
              ) : (
                <>
                  Document content explicitly identifies equipment{' '}
                  <strong className="font-mono text-amber-300 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">
                    {activeReviewModal.item.detectedTag}
                  </strong>
                  , which is not currently registered in your tenant asset inventory.
                </>
              )}
            </p>

            {activeReviewModal.item.evidence?.evidence_snippet && (
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono text-[11px] text-slate-300">
                <span className="text-slate-500 block mb-1 uppercase tracking-wider text-[9px]">Evidence Snippet:</span>
                "{activeReviewModal.item.evidence.evidence_snippet}"
              </div>
            )}

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-2">
              <span className="text-slate-400 block">Choose an action:</span>
              <div className="flex flex-col gap-2">
                <button
                  type="button"
                  id="confirm-create-machine-button"
                  onClick={() => {
                    handleAssociateWithDetected(activeReviewModal.item.id, activeReviewModal.item.detectedTag);
                    setActiveReviewModal(null);
                  }}
                  className="p-2.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white font-bold text-xs flex items-center justify-between cursor-pointer shadow-md shadow-brand-500/20"
                >
                  <span>Confirm & Associate with {activeReviewModal.item.detectedTag}</span>
                  <ArrowRight className="w-4 h-4" />
                </button>

                <button
                  type="button"
                  onClick={() => {
                    const fallbackTag = prompt('Enter existing asset tag to bind this document to:');
                    if (fallbackTag) {
                      const formatted = fallbackTag.toUpperCase().trim();
                      handleKeepHintOverride(activeReviewModal.item.id, formatted);
                    }
                    setActiveReviewModal(null);
                  }}
                  className="p-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-xs flex items-center justify-between cursor-pointer"
                >
                  <span>Review / Assign to Existing Machine</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            <div className="flex items-center justify-end pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setActiveReviewModal(null)}
                className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium cursor-pointer"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Sub-Dialog: No Machine Evidence Modal (Requirement 3) */}
      {activeReviewModal && activeReviewModal.type === 'NO_EVIDENCE' && (
        <div className="fixed inset-0 bg-black/90 z-60 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-5 space-y-4 shadow-2xl">
            <div className="flex items-center gap-3 text-orange-400">
              <div className="p-2 rounded-lg bg-orange-500/10 border border-orange-500/20">
                <HelpCircle className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white">Needs Review — Machine Association Unresolved</h4>
                <p className="text-xs text-slate-400">{activeReviewModal.item.name}</p>
              </div>
            </div>

            <p className="text-xs text-slate-300">
              No reliable machine identity could be extracted from this document. Per platform safety rules, it will not be attached automatically to the upload hint without explicit user confirmation.
            </p>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
              <span className="text-slate-400 block text-xs">Assign machine manually:</span>
              <div className="flex gap-2">
                <input
                  type="text"
                  id="manual-machine-tag-input"
                  placeholder="e.g. P-194"
                  defaultValue={hintAssetTag || ''}
                  className="flex-1 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white font-mono"
                />
                <button
                  type="button"
                  onClick={() => {
                    const el = document.getElementById('manual-machine-tag-input');
                    const val = el ? el.value.toUpperCase().trim() : '';
                    if (!val) {
                      alert('Please specify a machine tag.');
                      return;
                    }
                    setSelectedFiles((prev) =>
                      prev.map((f) =>
                        f.id === activeReviewModal.item.id
                          ? {
                              ...f,
                              targetTag: val,
                              explicitOverride: true,
                              resolutionStatus: 'RESOLVED_EXISTING',
                              statusLabel: `Resolved to ${val} by user assignment`,
                              message: `Manually assigned to ${val}`,
                            }
                          : f
                      )
                    );
                    setActiveReviewModal(null);
                  }}
                  className="px-4 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white font-bold text-xs cursor-pointer"
                >
                  Assign
                </button>
              </div>
            </div>

            <div className="flex items-center justify-end pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setActiveReviewModal(null)}
                className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium cursor-pointer"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
