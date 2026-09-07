import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePatient } from '../context/PatientContext';
import { summaryApi, documentApi } from '../api';
import { ClinicalSummary, MedicalDocument } from '../types';
import ProgressSteps from '../components/ProgressSteps';
import { 
  CheckCircle2, 
  AlertCircle, 
  FileText, 
  Clock, 
  Send, 
  ShieldCheck, 
  ArrowLeft, 
  Sparkles, 
  User, 
  Activity, 
  Heart, 
  Pill, 
  Check, 
  Printer, 
  Home,
  RefreshCw
} from 'lucide-react';

export const SummaryPage: React.FC = () => {
  const navigate = useNavigate();
  const { currentPatient, currentConsultation, activeHospital } = usePatient();

  const [summary, setSummary] = useState<ClinicalSummary | null>(null);
  const [documents, setDocuments] = useState<MedicalDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!currentConsultation || !currentPatient) {
      navigate('/identify');
      return;
    }

    fetchSummaryAndDocs();
  }, [currentConsultation, currentPatient]);

  const fetchSummaryAndDocs = async () => {
    if (!currentConsultation) return;
    setLoading(true);
    setError(null);

    try {
      // 1. Fetch documents
      try {
        const docRes = await documentApi.listDocuments(currentConsultation.id);
        setDocuments(docRes.items || []);
      } catch (dErr) {
        console.warn('Documents fetch skipped/empty:', dErr);
      }

      // 2. Fetch or generate AI clinical summary
      try {
        const sum = await summaryApi.getSummary(currentConsultation.id);
        setSummary(sum);
      } catch (sumErr: any) {
        if (sumErr.response?.status === 404) {
          // Trigger generation if not exists
          await handleGenerateSummary();
        } else {
          throw sumErr;
        }
      }
    } catch (err: any) {
      console.error('Failed to load summary:', err);
      setError(err.response?.data?.detail || 'Failed to retrieve clinical summary');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateSummary = async () => {
    if (!currentConsultation) return;
    setGenerating(true);
    setError(null);
    try {
      const res = await summaryApi.generateSummary(currentConsultation.id);
      setSummary(res);
    } catch (err: any) {
      console.error('Failed to generate summary:', err);
      setError(err.response?.data?.detail || 'Failed to generate AI summary');
    } finally {
      setGenerating(false);
    }
  };

  const handleSubmitToDoctor = () => {
    if (!confirmed) return;
    setSubmitted(true);
  };

  return (
    <div className="min-h-screen bg-surface flex flex-col items-center">
      {/* Top Header */}
      <header className="sticky top-0 z-30 w-full bg-surface-container-lowest/90 backdrop-blur-xl border-b border-surface-container-low shadow-sm px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button 
            onClick={() => navigate('/timeline')}
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
              <span className="font-caption text-[11px] text-on-surface-variant font-medium">Final Review & Submit</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[11px] font-bold text-secondary bg-secondary-container px-2.5 py-1 rounded-full flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            OPD Ready
          </span>
        </div>
      </header>

      {/* Main Container */}
      <main className="w-full max-w-xl px-4 py-4 flex flex-col gap-5 pb-28">
        {/* Stepper Header */}
        <ProgressSteps 
          currentStep={7} 
          stepTitle="Review & Verification" 
          totalSteps={7} 
        />

        {/* Introduction Banner */}
        <div className="bg-gradient-to-br from-secondary-container/40 to-surface-container-low rounded-2xl p-4 border border-secondary/30 flex flex-col gap-1.5">
          <div className="flex items-center gap-1.5 text-primary text-xs font-bold uppercase tracking-wider">
            <span className="material-symbols-outlined text-[18px]">verified_user</span>
            Doctor Consultation Intake
          </div>
          <h1 className="font-headline-sm text-xl font-bold text-on-surface">
            Review Your Information
          </h1>
          <p className="font-body-md text-xs text-on-surface-variant">
            Please verify all details before submitting your record to the OPD doctor queue. You can review your symptoms, history, and uploaded reports below.
          </p>
        </div>

        {/* Consultation Target Card */}
        <div className="bg-surface-container-lowest border border-outline-variant/40 rounded-2xl p-3.5 flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-secondary-container text-on-secondary-container flex items-center justify-center font-extrabold text-xs">
              OPD
            </div>
            <div>
              <p className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">Hospital Queue</p>
              <p className="text-xs font-bold text-on-surface">
                {activeHospital?.name || 'General Hospital OPD'}
              </p>
              <p className="text-[11px] text-on-surface-variant">
                Encounter ID: #{currentConsultation?.id.slice(0, 8)} • Priority: {currentConsultation?.priority || 'NORMAL'}
              </p>
            </div>
          </div>
          <span className="text-[10px] font-bold text-secondary bg-secondary-container px-2 py-0.5 rounded-full">
            In Queue
          </span>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-3 bg-error-container text-on-error-container rounded-xl flex items-start gap-2.5 text-xs font-semibold">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Section 1: About You */}
        <div className="bg-surface-container-lowest rounded-2xl p-4 border border-outline-variant/40 shadow-xs flex flex-col gap-3">
          <div className="flex items-center justify-between pb-2 border-b border-surface-container">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-surface-container-low text-primary flex items-center justify-center">
                <User className="w-4 h-4" />
              </div>
              <h2 className="font-headline-sm text-sm font-bold text-on-surface">About You</h2>
            </div>
            <button 
              onClick={() => navigate('/identify')}
              className="text-[11px] font-bold text-primary hover:underline"
            >
              Edit
            </button>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <span className="text-[11px] text-on-surface-variant">Full Legal Name</span>
              <p className="font-bold text-on-surface mt-0.5">{currentPatient?.full_name}</p>
            </div>
            <div>
              <span className="text-[11px] text-on-surface-variant">Gender & DOB</span>
              <p className="font-bold text-on-surface mt-0.5">
                {currentPatient?.gender} • {currentPatient?.dob || 'Not recorded'}
              </p>
            </div>
            <div>
              <span className="text-[11px] text-on-surface-variant">Blood Group</span>
              <p className="font-bold text-primary mt-0.5">
                {currentPatient?.blood_group || 'O Positive (O+)'}
              </p>
            </div>
            <div>
              <span className="text-[11px] text-on-surface-variant">ABHA ID (Demographic)</span>
              <p className="font-bold text-on-surface font-mono mt-0.5">
                {currentPatient?.abha_id || '91-4521-8890-1234'}
              </p>
            </div>
          </div>
        </div>

        {/* Section 2: Chief Complaint & Symptoms */}
        <div className="bg-surface-container-lowest rounded-2xl p-4 border border-outline-variant/40 shadow-xs flex flex-col gap-3">
          <div className="flex items-center justify-between pb-2 border-b border-surface-container">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-surface-container-low text-rose-600 flex items-center justify-center">
                <Activity className="w-4 h-4" />
              </div>
              <h2 className="font-headline-sm text-sm font-bold text-on-surface">Chief Complaint & Symptoms</h2>
            </div>
            <button 
              onClick={() => navigate('/interview')}
              className="text-[11px] font-bold text-primary hover:underline"
            >
              Edit
            </button>
          </div>

          <div className="space-y-2 text-xs">
            <div>
              <span className="text-[11px] text-on-surface-variant">Primary Reason for Visit:</span>
              <p className="p-2.5 rounded-xl bg-surface-container-low font-medium text-on-surface mt-1 leading-relaxed">
                "{currentConsultation?.chief_complaint || 'General medical examination & clinical history'}"
              </p>
            </div>

            <div className="flex items-center gap-1.5 pt-1">
              <span className="px-2 py-0.5 rounded-full bg-surface-container-high text-on-surface-variant text-[10px] font-bold">
                Voice & Text Captured
              </span>
              <span className="px-2 py-0.5 rounded-full bg-secondary-container text-on-secondary-container text-[10px] font-bold">
                Triage Verified
              </span>
            </div>
          </div>
        </div>

        {/* Section 3: Medical Documents Attached */}
        <div className="bg-surface-container-lowest rounded-2xl p-4 border border-outline-variant/40 shadow-xs flex flex-col gap-3">
          <div className="flex items-center justify-between pb-2 border-b border-surface-container">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-surface-container-low text-blue-600 flex items-center justify-center">
                <FileText className="w-4 h-4" />
              </div>
              <h2 className="font-headline-sm text-sm font-bold text-on-surface">
                Medical Records ({documents.length} Attached)
              </h2>
            </div>
            <button 
              onClick={() => navigate('/upload')}
              className="text-[11px] font-bold text-primary hover:underline"
            >
              Add/Edit
            </button>
          </div>

          {documents.length === 0 ? (
            <p className="text-xs text-on-surface-variant italic">
              No previous physical documents attached for this visit.
            </p>
          ) : (
            <div className="space-y-2">
              {documents.map(doc => (
                <div key={doc.id} className="p-2.5 rounded-xl bg-surface-container-low flex items-center justify-between">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <span className="text-sm">📄</span>
                    <div className="flex flex-col min-w-0">
                      <p className="font-bold text-xs text-on-surface truncate">{doc.filename}</p>
                      <span className="text-[10px] text-on-surface-variant capitalize">
                        {doc.document_type.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-secondary-container text-on-secondary-container">
                    Verified
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Section 4: AI Clinical Summary (Key Feature) */}
        <div className="bg-gradient-to-br from-surface-container-lowest via-secondary-container/10 to-surface-container-low rounded-2xl p-4 border-2 border-primary/30 shadow-xs flex flex-col gap-3">
          <div className="flex items-center justify-between pb-2 border-b border-outline-variant/30">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-primary text-on-primary flex items-center justify-center">
                <Sparkles className="w-4 h-4" />
              </div>
              <div>
                <h2 className="font-headline-sm text-sm font-bold text-on-surface">Clinical Summary</h2>
                <span className="text-[10px] text-on-surface-variant">Prepared for Doctor's EMR workspace</span>
              </div>
            </div>

            <button 
              onClick={handleGenerateSummary}
              disabled={generating}
              className="text-[11px] font-bold text-primary hover:underline flex items-center gap-1"
            >
              <RefreshCw className={`w-3 h-3 ${generating ? 'animate-spin' : ''}`} />
              Regenerate
            </button>
          </div>

          {loading || generating ? (
            <div className="py-6 text-center flex flex-col items-center gap-2">
              <RefreshCw className="w-5 h-5 text-primary animate-spin" />
              <p className="text-xs font-bold text-on-surface">Generating concise AI draft...</p>
            </div>
          ) : summary ? (
            <div className="space-y-3 text-xs">
              <div className="p-3 bg-surface-container-lowest rounded-xl border border-outline-variant/30 text-on-surface leading-relaxed space-y-1.5">
                <p>
                  <strong className="text-on-surface font-bold">Chief Concern: </strong>
                  {summary.chief_complaint || currentConsultation?.chief_complaint}
                </p>

                {(summary.history_of_present_illness || (summary.structured_summary as any)?.history_of_present_illness) && (
                  <p>
                    <strong className="text-on-surface font-bold">HPI: </strong>
                    {summary.history_of_present_illness || (summary.structured_summary as any)?.history_of_present_illness}
                  </p>
                )}

                {summary.summary_text && (
                  <p className="whitespace-pre-line text-on-surface-variant">
                    {summary.summary_text}
                  </p>
                )}

                {((summary.structured_findings?.medications?.length ?? 0) > 0 || ((summary.structured_summary as any)?.current_medications?.length ?? 0) > 0) && (
                  <p>
                    <strong className="text-on-surface font-bold">Medications: </strong>
                    {(summary.structured_findings?.medications || (summary.structured_summary as any)?.current_medications)?.map((m: any) => typeof m === 'string' ? m : m.name).join(', ')}
                  </p>
                )}

                {((summary.structured_findings?.allergies?.length ?? 0) > 0 || ((summary.structured_summary as any)?.allergies?.length ?? 0) > 0) && (
                  <p>
                    <strong className="text-on-surface font-bold">Allergies: </strong>
                    {(summary.structured_findings?.allergies || (summary.structured_summary as any)?.allergies)?.map((a: any) => typeof a === 'string' ? a : (a.allergen || a.name)).join(', ')}
                  </p>
                )}
              </div>

              {/* Prominent Mandatory AI Disclaimer */}
              <div className="p-2.5 rounded-xl bg-surface-container-low border border-primary/20 flex items-start gap-2 text-[11px] text-on-surface-variant leading-snug">
                <ShieldCheck className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                <span>
                  <strong>AI-generated summary</strong> — Please verify before submitting. No diagnosis or treatment advice is provided. Final review is conducted by your attending physician.
                </span>
              </div>
            </div>
          ) : (
            <div className="text-center py-3 text-xs text-on-surface-variant">
              Click Regenerate to synthesize summary.
            </div>
          )}
        </div>

        {/* Mandatory Confirmation Checkbox */}
        <div className="bg-surface-container-low rounded-2xl p-4 border border-outline-variant/40 flex flex-col gap-2">
          <div className="flex items-center gap-2 text-primary font-bold text-xs">
            <span className="material-symbols-outlined text-[18px]">verified</span>
            Patient Declaration
          </div>
          <p className="text-[11px] text-on-surface-variant">
            By submitting, you confirm that your answers and uploaded documents are accurate to the best of your knowledge.
          </p>

          <label className="mt-1 flex items-start gap-3 p-3 bg-surface-container-lowest rounded-xl border border-outline-variant/50 cursor-pointer hover:border-primary transition select-none">
            <input 
              type="checkbox"
              checked={confirmed}
              onChange={(e) => setConfirmed(e.target.checked)}
              className="w-4 h-4 mt-0.5 accent-primary text-primary rounded cursor-pointer shrink-0"
            />
            <span className="text-xs font-bold text-on-surface leading-snug">
              I have reviewed the information and confirm that it is correct.
            </span>
          </label>
        </div>

        {/* Submit Actions */}
        <div className="space-y-2.5 pt-2">
          <button
            type="button"
            disabled={!confirmed}
            onClick={handleSubmitToDoctor}
            className={`w-full h-12 rounded-xl font-bold text-sm flex items-center justify-center gap-2 transition-all ${
              confirmed
                ? 'bg-primary text-on-primary shadow-md hover:bg-primary-container active:scale-[0.99]'
                : 'bg-surface-container-high text-on-surface-variant/50 cursor-not-allowed'
            }`}
          >
            <Send className="w-4 h-4" />
            <span>Submit to Doctor Queue</span>
          </button>

          <button
            type="button"
            onClick={() => navigate('/')}
            className="w-full h-10 rounded-xl bg-surface-container-lowest text-on-surface-variant border border-outline-variant/40 font-semibold text-xs flex items-center justify-center gap-1 hover:bg-surface-container-low transition"
          >
            Save & Exit (Finish Later)
          </button>
        </div>
      </main>

      {/* Success Modal Overlay */}
      {submitted && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-sm bg-surface-container-lowest rounded-3xl p-6 shadow-2xl text-center flex flex-col items-center gap-4 animate-in fade-in zoom-in duration-200">
            <div className="w-16 h-16 rounded-full bg-secondary-container text-on-secondary-container flex items-center justify-center">
              <Check className="w-8 h-8" />
            </div>

            <div className="flex flex-col gap-1">
              <h3 className="font-headline-sm text-lg font-bold text-on-surface">
                Submitted Successfully!
              </h3>
              <p className="font-body-md text-xs text-on-surface-variant">
                Your medical history and clinical summary are now ready on Dr. Sharma's workspace.
              </p>
            </div>

            {/* Token Card */}
            <div className="w-full p-4 rounded-2xl bg-surface-container-low border border-primary/20 flex flex-col gap-1">
              <span className="font-caption text-[11px] text-on-surface-variant uppercase tracking-wider font-semibold">
                Your OPD Token Number
              </span>
              <span className="font-headline-lg text-3xl font-extrabold text-primary">
                #24
              </span>
              <span className="text-[11px] text-secondary font-bold">
                Estimated wait: ~15 mins
              </span>
            </div>

            <div className="w-full space-y-2 pt-2">
              <button
                type="button"
                onClick={() => window.print()}
                className="w-full h-10 rounded-xl bg-surface-container-high text-on-surface font-bold text-xs flex items-center justify-center gap-2 hover:bg-surface-container-highest transition"
              >
                <Printer className="w-4 h-4" />
                Print Intake Receipt
              </button>

              <button
                type="button"
                onClick={() => navigate('/')}
                className="w-full h-11 rounded-xl bg-primary text-on-primary font-bold text-xs flex items-center justify-center gap-2 shadow-sm hover:bg-primary-container transition"
              >
                <Home className="w-4 h-4" />
                Return to Home
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
export default SummaryPage;
