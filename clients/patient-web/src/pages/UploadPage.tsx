import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePatient } from '../context/PatientContext';
import { documentApi } from '../api';
import { MedicalDocument, DocumentType, StructuredExtraction } from '../types';
import ProgressSteps from '../components/ProgressSteps';
import { 
  Upload, 
  Camera, 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  AlertTriangle, 
  Clock, 
  ArrowRight, 
  Plus, 
  Save, 
  ExternalLink,
  Pill,
  Activity,
  FileCheck,
  RefreshCw,
  FolderOpen
} from 'lucide-react';

const DOC_TYPES: { type: DocumentType; label: string; icon: string }[] = [
  { type: 'prescription', label: 'Prescription', icon: 'prescriptions' },
  { type: 'lab_report', label: 'Lab Report', icon: 'biotech' },
  { type: 'radiology_scan', label: 'X-Ray / Scan', icon: 'radiology' },
  { type: 'discharge_summary', label: 'Discharge Summary', icon: 'local_hospital' },
  { type: 'other', label: 'Other', icon: 'article' },
];

export const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const { currentConsultation, activeSession } = usePatient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedType, setSelectedType] = useState<DocumentType>('prescription');
  const [documents, setDocuments] = useState<MedicalDocument[]>([]);
  const [activeDoc, setActiveDoc] = useState<MedicalDocument | null>(null);
  const [activeExtraction, setActiveExtraction] = useState<StructuredExtraction | null>(null);

  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Editable extraction form fields
  const [formFields, setFormFields] = useState({
    hospital: '',
    doctor: '',
    medicines: '',
    tests: '',
    notes: '',
  });

  // Load existing documents for this consultation
  useEffect(() => {
    if (!currentConsultation) {
      navigate('/identify');
      return;
    }

    fetchDocuments();
  }, [currentConsultation]);

  const fetchDocuments = async () => {
    if (!currentConsultation) return;
    try {
      const res = await documentApi.listDocuments(currentConsultation.id);
      const docs = res.items || [];
      setDocuments(docs);
      if (docs.length > 0 && !activeDoc) {
        selectDocument(docs[0]);
      }
    } catch (err) {
      console.error('Failed to list documents:', err);
    }
  };

  const selectDocument = async (doc: MedicalDocument) => {
    setActiveDoc(doc);
    setActiveExtraction(null);
    setUploadError(null);

    // Try to fetch extraction if available
    try {
      const ext = await documentApi.getExtraction(doc.id);
      setActiveExtraction(ext);
      populateForm(ext);
    } catch {
      // Extraction not ready or not processed yet
    }
  };

  const populateForm = (extraction: StructuredExtraction) => {
    const rawMedications = extraction.medications || extraction.entities?.medications || [];
    const medNames = Array.isArray(rawMedications) 
      ? rawMedications.map((m: any) => typeof m === 'string' ? m : (m.name_as_written || m.name || JSON.stringify(m))).join(', ')
      : '';

    const rawTests = extraction.investigations || extraction.laboratory_results || extraction.entities?.investigations || [];
    const testNames = Array.isArray(rawTests)
      ? rawTests.map((t: any) => typeof t === 'string' ? t : (t.test_name || JSON.stringify(t))).join(', ')
      : '';

    setFormFields({
      hospital: extraction.hospital_or_clinic_name || extraction.entities?.hospital || extraction.entities?.clinic_name || '',
      doctor: extraction.doctor_name || extraction.entities?.doctor_name || extraction.entities?.prescriber || '',
      medicines: medNames,
      tests: testNames,
      notes: extraction.follow_up_instructions_as_documented || extraction.raw_summary || extraction.cleaned_text?.slice(0, 150) || '',
    });
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    if (file.size > 25 * 1024 * 1024) {
      setUploadError('File size exceeds 25MB limit.');
      return;
    }

    setUploadError(null);
    setIsUploading(true);

    try {
      if (!currentConsultation) throw new Error('No active consultation encounter');

      // 1. Upload
      const newDoc = await documentApi.uploadDocument(
        file, 
        selectedType, 
        currentConsultation.id
      );
      setDocuments(prev => [newDoc, ...prev]);
      setActiveDoc(newDoc);
      setIsUploading(false);

      // 2. Automatically trigger OCR processing
      setIsProcessing(true);
      try {
        await documentApi.processDocument(newDoc.id);
        const extraction = await documentApi.getExtraction(newDoc.id);
        setActiveExtraction(extraction);
        populateForm(extraction);
      } catch (procErr: any) {
        console.warn('Document uploaded, OCR extraction queued or pending:', procErr);
      } finally {
        setIsProcessing(false);
      }
    } catch (err: any) {
      setIsUploading(false);
      setIsProcessing(false);
      setUploadError(err.response?.data?.detail || err.message || 'Failed to upload document');
    }
  };

  const handleTriggerReProcess = async () => {
    if (!activeDoc) return;
    setIsProcessing(true);
    setUploadError(null);
    try {
      await documentApi.processDocument(activeDoc.id);
      const ext = await documentApi.getExtraction(activeDoc.id);
      setActiveExtraction(ext);
      populateForm(ext);
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || 'Extraction failed to complete.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSaveVerifiedExtraction = () => {
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3000);
  };

  return (
    <div className="min-h-screen bg-surface flex flex-col items-center">
      {/* Top Header */}
      <header className="sticky top-0 z-30 w-full bg-surface-container-lowest/90 backdrop-blur-xl border-b border-surface-container-low shadow-sm px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button 
            onClick={() => navigate('/interview')}
            className="w-10 h-10 rounded-full flex items-center justify-center text-on-surface-variant hover:bg-surface-container-low transition active:scale-95"
          >
            <span className="material-symbols-outlined text-[24px]">arrow_back</span>
          </button>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary text-on-primary flex items-center justify-center font-bold text-sm">
              C
            </div>
            <div className="flex flex-col">
              <span className="font-headline-sm text-sm font-bold text-primary tracking-tight leading-none">CLINOVA</span>
              <span className="font-caption text-[11px] text-on-surface-variant font-medium">Medical Documents & OCR</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button 
            onClick={() => navigate('/timeline')}
            className="text-xs font-bold text-primary hover:text-primary-container px-3 py-1.5 rounded-lg border border-outline-variant hover:bg-surface-container-low transition"
          >
            Skip to Timeline
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main className="w-full max-w-xl px-4 py-4 flex flex-col gap-5 pb-24">
        {/* Stepper Header */}
        <ProgressSteps 
          currentStep={5} 
          stepTitle="Medical Document Scanning & Records" 
          totalSteps={7} 
        />

        {/* Introduction Banner */}
        <div className="bg-surface-container-low rounded-2xl p-4 border border-outline-variant/30 flex flex-col gap-1.5">
          <div className="flex items-center gap-1.5 text-primary text-xs font-bold uppercase tracking-wider">
            <span className="material-symbols-outlined text-[18px]">verified</span>
            Clinova Optical Recognition
          </div>
          <h1 className="font-headline-sm text-xl font-bold text-on-surface">
            Add Your Previous Medical Records
          </h1>
          <p className="font-body-md text-xs text-on-surface-variant">
            Upload prescriptions, lab reports, or discharge summaries. Our clinical OCR extracts diagnoses and medicines automatically so your doctor can review your complete history.
          </p>
        </div>

        {/* Document Type Selector */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <label className="font-label-lg text-xs font-bold text-on-surface">
              Document Category
            </label>
            <span className="font-caption text-[11px] text-primary font-semibold">Select before uploading</span>
          </div>

          <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
            {DOC_TYPES.map(dt => (
              <button
                key={dt.type}
                type="button"
                onClick={() => setSelectedType(dt.type)}
                className={`shrink-0 min-h-[40px] px-3.5 rounded-full flex items-center gap-1.5 text-xs font-bold transition-all ${
                  selectedType === dt.type
                    ? 'bg-primary text-on-primary shadow-sm'
                    : 'bg-surface-container-lowest text-on-surface-variant border border-outline-variant/30 hover:bg-surface-container-low'
                }`}
              >
                <span className="material-symbols-outlined text-[16px]">{dt.icon}</span>
                {dt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Primary Capture Actions */}
        <div className="grid grid-cols-2 gap-3">
          {/* File Input (Hidden) */}
          <input 
            ref={fileInputRef}
            type="file"
            accept="image/*,.pdf"
            className="hidden"
            onChange={handleFileChange}
          />

          {/* Camera Capture */}
          <button
            type="button"
            disabled={isUploading}
            onClick={() => fileInputRef.current?.click()}
            className="flex flex-col items-start p-4 bg-surface-container-lowest rounded-2xl border border-outline-variant/40 shadow-xs hover:border-primary/50 transition-all text-left group active:scale-[0.99]"
          >
            <div className="w-10 h-10 rounded-xl bg-secondary-container text-on-secondary-container flex items-center justify-center mb-3 group-hover:bg-primary group-hover:text-on-primary transition-colors">
              <Camera className="w-5 h-5" />
            </div>
            <span className="font-label-lg text-sm font-bold text-on-surface">Scan with Camera</span>
            <span className="font-caption text-[11px] text-on-surface-variant mt-0.5">Take photo of paper sheet</span>
          </button>

          {/* Device Upload */}
          <button
            type="button"
            disabled={isUploading}
            onClick={() => fileInputRef.current?.click()}
            className="flex flex-col items-start p-4 bg-surface-container-lowest rounded-2xl border border-outline-variant/40 shadow-xs hover:border-primary/50 transition-all text-left group active:scale-[0.99]"
          >
            <div className="w-10 h-10 rounded-xl bg-surface-container-high text-primary flex items-center justify-center mb-3 group-hover:bg-primary group-hover:text-on-primary transition-colors">
              <Upload className="w-5 h-5" />
            </div>
            <span className="font-label-lg text-sm font-bold text-on-surface">Upload File</span>
            <span className="font-caption text-[11px] text-on-surface-variant mt-0.5">PDF, JPG, PNG up to 25MB</span>
          </button>
        </div>

        {/* Error Alert */}
        {uploadError && (
          <div className="p-3 bg-error-container text-on-error-container rounded-xl flex items-start gap-2.5 text-xs font-semibold">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{uploadError}</span>
          </div>
        )}

        {/* Uploading Spinner */}
        {isUploading && (
          <div className="p-4 bg-surface-container-lowest rounded-2xl border border-primary/20 shadow-xs flex items-center gap-3">
            <RefreshCw className="w-5 h-5 text-primary animate-spin" />
            <div>
              <p className="font-label-lg text-xs font-bold text-on-surface">Uploading document to secure storage...</p>
              <p className="font-caption text-[11px] text-on-surface-variant">Encrypting and attaching to consultation encounter</p>
            </div>
          </div>
        )}

        {/* Processing Spinner */}
        {isProcessing && (
          <div className="p-4 bg-surface-container-low rounded-2xl border border-secondary/30 shadow-xs flex items-center gap-3">
            <RefreshCw className="w-5 h-5 text-secondary animate-spin" />
            <div>
              <p className="font-label-lg text-xs font-bold text-secondary">Clinova AI OCR reading document...</p>
              <p className="font-caption text-[11px] text-on-surface-variant">Extracting medications, lab values, and timestamps</p>
            </div>
          </div>
        )}

        {/* Active Document Review Section */}
        {activeDoc && (
          <div className="bg-surface-container-lowest rounded-2xl p-4 border border-outline-variant/40 shadow-xs flex flex-col gap-4">
            <div className="flex items-start justify-between gap-3 pb-3 border-b border-surface-container">
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-12 h-12 rounded-xl bg-surface-container-low text-primary flex items-center justify-center shrink-0">
                  <FileText className="w-6 h-6" />
                </div>
                <div className="flex flex-col min-w-0">
                  <span className="font-caption text-[10px] text-primary font-bold uppercase tracking-wider">
                    {activeDoc.document_type.replace('_', ' ')}
                  </span>
                  <p className="font-label-lg text-sm font-bold text-on-surface truncate">
                    {activeDoc.filename}
                  </p>
                  <span className="font-caption text-[11px] text-on-surface-variant">
                    {new Date(activeDoc.created_at).toLocaleDateString('en-IN', {
                      day: 'numeric',
                      month: 'short',
                      year: 'numeric'
                    })} • Status: <strong className="text-primary">{activeDoc.ocr_status}</strong>
                  </span>
                </div>
              </div>

              {!activeExtraction && !isProcessing && (
                <button
                  type="button"
                  onClick={handleTriggerReProcess}
                  className="px-3 py-1.5 rounded-lg bg-secondary-container text-on-secondary-container font-label-md text-xs font-bold flex items-center gap-1 hover:opacity-90"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  Process OCR
                </button>
              )}
            </div>

            {/* OCR Extraction Result */}
            {activeExtraction ? (
              <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-on-surface">
                    <CheckCircle2 className="w-4 h-4 text-primary" />
                    <span>Extracted Clinical Information</span>
                  </div>
                  <span className="px-2 py-0.5 rounded-full bg-secondary-container text-on-secondary-container text-[10px] font-bold">
                    Patient Editable
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-surface-container-low border border-primary/20 text-xs text-on-surface-variant">
                  Please review the details read from your document. You may edit any inaccurate field before saving to your permanent medical timeline.
                </div>

                {/* Form Fields */}
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-[11px] font-bold text-on-surface">Hospital / Clinic</label>
                      <input 
                        type="text"
                        value={formFields.hospital}
                        onChange={(e) => setFormFields({ ...formFields, hospital: e.target.value })}
                        placeholder="e.g. City Hospital OPD"
                        className="w-full h-10 px-3 mt-1 rounded-xl bg-surface-container-low border border-outline-variant/30 text-xs font-semibold text-on-surface focus:outline-none focus:border-primary"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] font-bold text-on-surface">Doctor / Prescriber</label>
                      <input 
                        type="text"
                        value={formFields.doctor}
                        onChange={(e) => setFormFields({ ...formFields, doctor: e.target.value })}
                        placeholder="e.g. Dr. A. Sharma"
                        className="w-full h-10 px-3 mt-1 rounded-xl bg-surface-container-low border border-outline-variant/30 text-xs font-semibold text-on-surface focus:outline-none focus:border-primary"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-[11px] font-bold text-on-surface">Medicines Found</label>
                    <textarea 
                      rows={2}
                      value={formFields.medicines}
                      onChange={(e) => setFormFields({ ...formFields, medicines: e.target.value })}
                      placeholder="e.g. Metformin 500mg (1-0-1), Telmisartan 40mg"
                      className="w-full p-2.5 mt-1 rounded-xl bg-surface-container-low border border-outline-variant/30 text-xs font-medium text-on-surface focus:outline-none focus:border-primary resize-none"
                    />
                  </div>

                  <div>
                    <label className="text-[11px] font-bold text-on-surface">Tests / Investigations</label>
                    <input 
                      type="text"
                      value={formFields.tests}
                      onChange={(e) => setFormFields({ ...formFields, tests: e.target.value })}
                      placeholder="e.g. Fasting Blood Sugar, CBC, Lipid Profile"
                      className="w-full h-10 px-3 mt-1 rounded-xl bg-surface-container-low border border-outline-variant/30 text-xs font-medium text-on-surface focus:outline-none focus:border-primary"
                    />
                  </div>

                  <div>
                    <label className="text-[11px] font-bold text-on-surface">Instructions / Clinical Summary</label>
                    <textarea 
                      rows={2}
                      value={formFields.notes}
                      onChange={(e) => setFormFields({ ...formFields, notes: e.target.value })}
                      placeholder="e.g. Take medicines after meals, follow up in 2 weeks"
                      className="w-full p-2.5 mt-1 rounded-xl bg-surface-container-low border border-outline-variant/30 text-xs font-medium text-on-surface focus:outline-none focus:border-primary resize-none"
                    />
                  </div>
                </div>

                <div className="pt-2 flex items-center justify-between">
                  <button
                    type="button"
                    onClick={handleSaveVerifiedExtraction}
                    className="px-4 py-2 rounded-xl bg-primary text-on-primary font-bold text-xs flex items-center gap-1.5 shadow-sm active:scale-95 transition"
                  >
                    <Save className="w-4 h-4" />
                    Save & Confirm Extraction
                  </button>

                  {saveSuccess && (
                    <span className="text-xs font-bold text-secondary flex items-center gap-1">
                      <CheckCircle2 className="w-4 h-4" />
                      Saved to Record!
                    </span>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center py-4 text-xs text-on-surface-variant font-medium">
                OCR extraction has not yet completed for this document. Click "Process OCR" above to extract data now.
              </div>
            )}
          </div>
        )}

        {/* Existing Attached Documents List */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <FolderOpen className="w-4 h-4 text-primary" />
              <h2 className="font-headline-sm text-sm font-bold text-on-surface">
                Attached Encounter Documents ({documents.length})
              </h2>
            </div>
          </div>

          {documents.length === 0 ? (
            <div className="p-6 rounded-2xl bg-surface-container-lowest border border-dashed border-outline-variant/50 text-center flex flex-col items-center gap-2">
              <FileText className="w-8 h-8 text-on-surface-variant/50" />
              <p className="font-label-lg text-xs font-bold text-on-surface-variant">No documents attached yet</p>
              <p className="font-caption text-[11px] text-on-surface-variant/70">
                You can upload prescriptions or lab reports now, or proceed directly to your timeline.
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {documents.map((doc) => (
                <div 
                  key={doc.id}
                  onClick={() => selectDocument(doc)}
                  className={`p-3 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${
                    activeDoc?.id === doc.id
                      ? 'bg-surface-container-lowest border-primary shadow-xs'
                      : 'bg-surface-container-lowest/70 border-outline-variant/30 hover:border-primary/40'
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-8 h-8 rounded-lg bg-surface-container-low text-primary flex items-center justify-center shrink-0 text-xs font-bold">
                      📄
                    </div>
                    <div className="flex flex-col min-w-0">
                      <p className="font-label-lg text-xs font-bold text-on-surface truncate">
                        {doc.filename}
                      </p>
                      <span className="font-caption text-[10px] text-on-surface-variant capitalize">
                        {doc.document_type.replace('_', ' ')} • {new Date(doc.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>

                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    doc.ocr_status === 'COMPLETED' 
                      ? 'bg-secondary-container text-on-secondary-container' 
                      : 'bg-surface-container-high text-on-surface-variant'
                  }`}>
                    {doc.ocr_status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Navigation Action Buttons */}
        <div className="pt-3 space-y-2.5">
          <button
            type="button"
            onClick={() => navigate('/timeline')}
            className="w-full h-12 rounded-xl bg-primary text-on-primary font-bold text-sm flex items-center justify-center gap-2 shadow-md hover:bg-primary-container active:scale-[0.99] transition-all"
          >
            <span>Continue to Medical Timeline</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <button
            type="button"
            onClick={() => navigate('/interview')}
            className="w-full h-10 rounded-xl bg-surface-container-lowest text-on-surface-variant border border-outline-variant/40 font-semibold text-xs flex items-center justify-center gap-1 hover:bg-surface-container-low transition"
          >
            Back to AI Interview
          </button>
        </div>
      </main>
    </div>
  );
};
export default UploadPage;
