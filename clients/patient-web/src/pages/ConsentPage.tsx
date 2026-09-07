import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import ProgressSteps from '../components/ProgressSteps';
import { usePatient } from '../context/PatientContext';
import { consultationApi } from '../api';
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle,
  ArrowRight,
  ArrowLeft,
  Bot,
  UserCheck,
  Lock,
  FileCheck2,
} from 'lucide-react';

const CONSENT_POINTS = [
  {
    icon: <Bot className="w-5 h-5 text-primary" />,
    title: 'AI-Assisted Adaptive Interview',
    desc: 'Your responses will be processed by an AI clinical intake engine to ask relevant follow-up questions and structure your symptoms.',
  },
  {
    icon: <UserCheck className="w-5 h-5 text-secondary" />,
    title: 'Physician Authority & Review',
    desc: 'The AI does not formulate diagnoses or prescribe treatments. Your attending OPD doctor will review and verify all information.',
  },
  {
    icon: <Lock className="w-5 h-5 text-tertiary" />,
    title: 'Data Privacy & Tenant Isolation',
    desc: 'Your clinical records are encrypted and strictly isolated to this hospital facility under digital health privacy regulations.',
  },
  {
    icon: <FileCheck2 className="w-5 h-5 text-primary" />,
    title: 'Document OCR & Extraction',
    desc: 'Old prescriptions and lab reports you choose to upload will be processed via optical recognition to create a chronological timeline.',
  },
];

export const ConsentPage: React.FC = () => {
  const navigate = useNavigate();
  const { patient, activeConsultation, setConsentGiven } = usePatient();

  const [agreed, setAgreed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Protect route if patient or consultation missing
  if (!patient || !activeConsultation) {
    navigate('/identify');
    return null;
  }

  const handleRecordConsent = async () => {
    if (!agreed) return;
    setLoading(true);
    setError('');

    try {
      // Call backend explicit consent endpoint
      await consultationApi.recordConsent(activeConsultation.id, {
        consent_given: true,
        consent_type: 'clinical_intake',
      });

      setConsentGiven(true);
      navigate('/language');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to record consent. Please try again.';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface flex flex-col">
      <Navbar />

      <main className="max-w-2xl w-full mx-auto px-4 py-8 flex-1 flex flex-col">
        <ProgressSteps currentStepIndex={1} />

        <div className="card-elevated p-6 sm:p-8 bg-surface-container-lowest flex flex-col">
          {/* Header */}
          <div className="text-center mb-6">
            <div className="w-14 h-14 rounded-2xl bg-secondary-container/60 text-secondary flex items-center justify-center mx-auto mb-3 shadow-xs">
              <ShieldCheck className="w-7 h-7" />
            </div>
            <h1 className="text-2xl font-black text-on-surface tracking-tight">
              Informed Patient Consent
            </h1>
            <p className="text-xs sm:text-sm text-on-surface-variant mt-1">
              Please review the clinical intake and data processing terms for{' '}
              <strong className="text-on-surface">{patient.full_name}</strong>
            </p>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-xl bg-error-container/50 border border-error/30 text-on-error-container text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-error shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Consent Points Grid */}
          <div className="space-y-3 mb-6">
            {CONSENT_POINTS.map((pt, i) => (
              <div
                key={i}
                className="p-4 rounded-xl bg-surface-container-low/60 border border-outline-variant/30 flex items-start gap-3.5"
              >
                <div className="w-9 h-9 rounded-lg bg-surface-container-lowest flex items-center justify-center shrink-0 shadow-xs">
                  {pt.icon}
                </div>
                <div className="flex flex-col">
                  <h3 className="text-sm font-bold text-on-surface">{pt.title}</h3>
                  <p className="text-xs text-on-surface-variant mt-0.5 leading-relaxed">
                    {pt.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {/* Disclaimer Banner */}
          <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 flex items-start gap-3 mb-6">
            <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <p className="text-xs leading-relaxed">
              <strong>Medical Disclaimer:</strong> Clinova is an assistive software tool designed to organize patient history for attending clinicians. All clinical decisions, evaluations, and treatments are conducted exclusively by licensed physicians.
            </p>
          </div>

          {/* Checkbox Agreement */}
          <label
            className={`flex items-start gap-3 p-4 rounded-xl border-2 cursor-pointer transition-all mb-6 ${
              agreed
                ? 'bg-secondary-container/20 border-primary'
                : 'bg-surface-container-lowest border-outline-variant/50 hover:bg-surface-container-low/40'
            }`}
          >
            <input 
              type="checkbox"
              checked={agreed}
              onChange={(e) => setAgreed(e.target.checked)}
              className="sr-only"
            />
            <div
              className={`w-5 h-5 rounded-md border flex items-center justify-center shrink-0 mt-0.5 transition-colors ${
                agreed ? 'bg-primary border-primary text-on-primary' : 'border-outline bg-surface-container-lowest'
              }`}
            >
              {agreed && <CheckCircle className="w-3.5 h-3.5" />}
            </div>
            <div className="text-xs text-on-surface leading-relaxed select-none">
              I, <strong>{patient.full_name}</strong>, have read and understand the above information. I hereby grant informed consent for Clinova to process my clinical intake responses and medical documents for my consultation today.
            </div>
          </label>

          {/* Action Buttons */}
          <div className="flex items-center gap-3 mt-auto pt-2">
            <button
              type="button"
              onClick={() => navigate('/identify')}
              className="flex-1 min-h-[48px] px-4 rounded-xl border border-outline-variant/60 text-on-surface font-semibold text-xs hover:bg-surface-container transition-colors flex items-center justify-center gap-1.5"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back</span>
            </button>

            <button
              type="button"
              onClick={handleRecordConsent}
              disabled={!agreed || loading}
              className="flex-[2] min-h-[48px] px-6 rounded-xl bg-primary text-on-primary font-bold text-sm shadow-md hover:bg-primary-container transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span>Recording Server Consent...</span>
              ) : (
                <>
                  <span>I Agree • Continue</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default ConsentPage;
