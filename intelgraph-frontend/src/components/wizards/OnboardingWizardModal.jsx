import React, { useState } from 'react';
import { 
  X, 
  Upload, 
  FileText, 
  CheckCircle2, 
  AlertTriangle, 
  UserCheck, 
  ArrowRight, 
  Sparkles,
  Layers
} from 'lucide-react';
import { api } from '../../services/api';
import InformationBadge from '../common/InformationBadge';

export default function OnboardingWizardModal({ defaultAssetTag = 'P-101', onClose, onCompleted }) {
  const [step, setStep] = useState(1); // 1: Upload, 2: Processing, 3: Human Confirmation, 4: Success
  const [assetTag, setAssetTag] = useState(defaultAssetTag);
  const [category, setCategory] = useState('Maintenance');
  const [version, setVersion] = useState('v1.0');
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadedDoc, setUploadedDoc] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Editable confirmation fields
  const [confirmedTag, setConfirmedTag] = useState(defaultAssetTag);
  const [confirmedEvent, setConfirmedEvent] = useState('Maintenance');
  const [confirmedDate, setConfirmedDate] = useState('2026-03-01');
  const [confirmedComponent, setConfirmedComponent] = useState('Bearing');
  const [confirmedWorkOrder, setConfirmedWorkOrder] = useState('WO-2026-01');
  const [confirmedBy, setConfirmedBy] = useState('Lead Maintenance Engineer');

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUploadAndExtract = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      alert('Please select a document to upload');
      return;
    }

    setStep(2);
    setIsProcessing(true);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('asset_tag', assetTag);
      formData.append('category', category);
      formData.append('version', version);
      formData.append('governance_status', 'Approved');
      formData.append('uploaded_by', confirmedBy);

      const docRes = await api.uploadDocument(formData);
      setUploadedDoc(docRes);

      // Populate confirmation staging from extracted entities
      const entities = docRes.extracted_entities || {};
      setConfirmedTag(entities.primary_asset_tag !== 'Unknown' ? entities.primary_asset_tag : assetTag);
      setConfirmedEvent(entities.event_type || category);
      setConfirmedDate(entities.primary_date !== 'Unknown' ? entities.primary_date : '2026-03-01');
      setConfirmedComponent(entities.primary_component || 'Drive-End Bearing');
      setConfirmedWorkOrder(entities.work_orders?.[0] || 'WO-1023');

      setStep(3); // Move to Human Confirmation step!
    } catch (err) {
      alert('Document processing failed: ' + err.message);
      setStep(1);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleConfirmExtraction = async () => {
    if (!uploadedDoc) return;
    setIsProcessing(true);
    try {
      const form = new FormData();
      form.append('document_id', uploadedDoc.document_id);
      form.append('confirmed_asset_tag', confirmedTag);
      form.append('event_type', confirmedEvent);
      form.append('event_date', confirmedDate);
      form.append('component', confirmedComponent);
      form.append('work_order', confirmedWorkOrder);
      form.append('confirmed_by', confirmedBy);

      await api.confirmExtraction(form);
      setStep(4);
      if (onCompleted) onCompleted(confirmedTag);
    } catch (err) {
      alert('Confirmation failed: ' + err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-brand-500/10 text-brand-400 border border-brand-500/20">
              <Upload className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <span>Import Existing Asset Knowledge (Use Case 1)</span>
              </h3>
              <p className="text-xs text-slate-400">
                Legacy document ingestion with mandatory human-in-the-loop verification
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

        {/* Wizard Steps Indicator */}
        <div className="px-6 py-2.5 bg-slate-950/60 border-b border-slate-800 flex items-center justify-between text-[11px] font-mono">
          <span className={step >= 1 ? 'text-brand-400 font-bold' : 'text-slate-400'}>1. Upload File</span>
          <ArrowRight className="w-3 h-3 text-slate-400" />
          <span className={step >= 2 ? 'text-brand-400 font-bold' : 'text-slate-400'}>2. AI Extraction</span>
          <ArrowRight className="w-3 h-3 text-slate-400" />
          <span className={step >= 3 ? 'text-amber-400 font-bold' : 'text-slate-400'}>3. Human Confirmation</span>
          <ArrowRight className="w-3 h-3 text-slate-400" />
          <span className={step >= 4 ? 'text-emerald-400 font-bold' : 'text-slate-400'}>4. Knowledge Saved</span>
        </div>

        {/* STEP 1: Upload */}
        {step === 1 && (
          <form onSubmit={handleUploadAndExtract} className="p-6 space-y-4 text-xs">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-400 mb-1 font-medium">Target Asset Tag *</label>
                <input
                  type="text"
                  required
                  value={assetTag}
                  onChange={(e) => setAssetTag(e.target.value.toUpperCase())}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white font-mono focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">Document Category *</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-brand-500"
                >
                  <option value="Maintenance">Maintenance Report / Work Order</option>
                  <option value="OEM Manual">OEM Technical Manual</option>
                  <option value="SOP">Standard Operating Procedure</option>
                  <option value="Inspection">Condition Monitoring / Inspection</option>
                  <option value="Incident">Failure / Incident Report</option>
                  <option value="Engineering">Engineering Drawing / Spec</option>
                  <option value="Safety">Safety & LOTO Procedure</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-slate-400 mb-1 font-medium">Governance Version</label>
              <input
                type="text"
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 font-mono focus:outline-none focus:border-brand-500"
              />
            </div>

            {/* File Upload Zone */}
            <div className="border-2 border-dashed border-slate-700 hover:border-brand-500 rounded-xl p-6 text-center space-y-2 bg-slate-950/40 transition-colors">
              <FileText className="w-8 h-8 text-slate-400 mx-auto" />
              <div className="text-xs text-slate-300 font-medium">
                {selectedFile ? selectedFile.name : 'Choose a legacy industrial file (PDF, DOCX, XLSX, CSV)'}
              </div>
              <p className="text-[11px] text-slate-400">
                Example: P101_Maintenance_2024.pdf or Pump_OEM_Manual.pdf
              </p>
              <label className="inline-block px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-brand-400 text-xs font-semibold cursor-pointer border border-slate-700 transition-all">
                Browse File
                <input
                  type="file"
                  onChange={handleFileChange}
                  accept=".pdf,.docx,.xlsx,.csv,.txt"
                  className="hidden"
                />
              </label>
            </div>

            <div className="pt-2 border-t border-slate-800 flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-all"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!selectedFile}
                className="px-5 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-white font-bold text-xs transition-all shadow-md shadow-brand-500/20 disabled:opacity-50"
              >
                Process & Extract
              </button>
            </div>
          </form>
        )}

        {/* STEP 2: Processing State */}
        {step === 2 && (
          <div className="p-12 text-center space-y-3">
            <div className="w-9 h-9 border-2 border-brand-400 border-t-transparent rounded-full animate-spin mx-auto"></div>
            <h4 className="text-sm font-bold text-white">Extracting Industrial Information...</h4>
            <p className="text-xs text-slate-400 max-w-xs mx-auto">
              Scanning document pages, chunking sections, generating FAISS embeddings, and identifying equipment tags.
            </p>
          </div>
        )}

        {/* STEP 3: HUMAN CONFIRMATION (Critical Spec Rule) */}
        {step === 3 && (
          <div className="p-6 space-y-4 text-xs">
            <div className="p-3.5 rounded-xl bg-amber-950/25 border border-amber-500/30 flex items-start gap-2.5 text-amber-300">
              <UserCheck className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <strong className="font-semibold text-amber-200">Human Verification Step:</strong>
                <p className="text-[11px] text-amber-300/90 mt-0.5">
                  Industrial records must not be blindly accepted from AI. Please confirm or edit the extracted parameters before committing to the asset profile.
                </p>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 border-b border-slate-800/80 pb-2">
                <span>Extracted from: {uploadedDoc?.filename}</span>
                <span className="text-brand-400">Confidence: High</span>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Canonical Asset Tag</label>
                  <input
                    type="text"
                    value={confirmedTag}
                    onChange={(e) => setConfirmedTag(e.target.value)}
                    className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white font-mono focus:border-brand-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Event Type</label>
                  <input
                    type="text"
                    value={confirmedEvent}
                    onChange={(e) => setConfirmedEvent(e.target.value)}
                    className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white focus:border-brand-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Event Date</label>
                  <input
                    type="text"
                    value={confirmedDate}
                    onChange={(e) => setConfirmedDate(e.target.value)}
                    className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white font-mono focus:border-brand-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Primary Component</label>
                  <input
                    type="text"
                    value={confirmedComponent}
                    onChange={(e) => setConfirmedComponent(e.target.value)}
                    className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white focus:border-brand-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">Work Order / Record Reference</label>
                <input
                  type="text"
                  value={confirmedWorkOrder}
                  onChange={(e) => setConfirmedWorkOrder(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white font-mono focus:border-brand-500"
                />
              </div>
            </div>

            <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
              >
                Re-upload
              </button>
              <button
                onClick={handleConfirmExtraction}
                disabled={isProcessing}
                className="px-5 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold text-xs flex items-center gap-1.5 transition-all shadow-md shadow-emerald-500/20"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>Confirm & Commit to Asset</span>
              </button>
            </div>
          </div>
        )}

        {/* STEP 4: Success */}
        {step === 4 && (
          <div className="p-8 text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">
                Knowledge Profile Updated!
              </h3>
              <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                Verified event committed for <strong className="text-brand-400">{confirmedTag}</strong>: {confirmedEvent} on {confirmedComponent} ({confirmedDate}).
              </p>
            </div>

            <div className="pt-3 flex justify-center gap-3">
              <button
                onClick={onClose}
                className="px-5 py-2 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-semibold text-xs transition-all shadow-lg shadow-brand-500/20"
              >
                Close & View Asset Profile
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
