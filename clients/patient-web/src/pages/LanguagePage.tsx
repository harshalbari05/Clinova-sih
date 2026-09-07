import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import ProgressSteps from '../components/ProgressSteps';
import { usePatient } from '../context/PatientContext';
import { aiApi } from '../api';
import {
  Languages,
  Check,
  ArrowRight,
  ArrowLeft,
  Stethoscope,
  Leaf,
  AlertCircle,
  Sparkles,
} from 'lucide-react';

const LANGUAGE_OPTIONS = [
  {
    id: 'English',
    name: 'English',
    nativeName: 'English',
    flag: '🇮🇳',
    desc: 'Voice & Text',
  },
  {
    id: 'Hindi',
    name: 'Hindi',
    nativeName: 'हिन्दी',
    flag: '🇮🇳',
    desc: 'आवाज़ और टेक्स्ट',
  },
  {
    id: 'Marathi',
    name: 'Marathi',
    nativeName: 'मराठी',
    flag: '🇮🇳',
    desc: 'आवाज आणि मजकूर',
  },
];

export const LanguagePage: React.FC = () => {
  const navigate = useNavigate();
  const {
    patient,
    activeConsultation,
    language,
    setLanguage,
    setActiveSession,
  } = usePatient();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Protect route
  if (!patient || !activeConsultation) {
    navigate('/identify');
    return null;
  }

  const handleStartSession = async () => {
    setLoading(true);
    setError('');

    try {
      // 1. Create AI Session on backend
      const session = await aiApi.createSession(activeConsultation.id, language);
      setActiveSession(session);

      // 2. Navigate to Interview
      navigate('/interview');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to start AI interview session. Please try again.';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface flex flex-col">
      <Navbar />

      <main className="max-w-2xl w-full mx-auto px-4 py-8 flex-1 flex flex-col">
        <ProgressSteps currentStepIndex={2} />

        <div className="card-elevated p-6 sm:p-8 bg-surface-container-lowest flex flex-col">
          {/* Header */}
          <div className="text-center mb-6">
            <div className="w-14 h-14 rounded-2xl bg-secondary-container/60 text-secondary flex items-center justify-center mx-auto mb-3 shadow-xs">
              <Languages className="w-7 h-7" />
            </div>
            <h1 className="text-2xl font-black text-on-surface tracking-tight">
              Select Your Preferred Language
            </h1>
            <p className="text-xs sm:text-sm text-on-surface-variant mt-1">
              Choose the language you want the AI assistant to use during your interview
            </p>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-xl bg-error-container/50 border border-error/30 text-on-error-container text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-error shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Language Selection Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
            {LANGUAGE_OPTIONS.map((lang) => {
              const isSelected = language === lang.id;
              return (
                <button
                  key={lang.id}
                  type="button"
                  onClick={() => setLanguage(lang.id)}
                  className={`p-4 rounded-xl border-2 text-left flex flex-col justify-between transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-secondary-container/20 border-primary shadow-sm ring-2 ring-primary/10'
                      : 'bg-surface-container-low/40 border-outline-variant/40 hover:bg-surface-container-low'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xl">{lang.flag}</span>
                    {isSelected && (
                      <div className="w-5 h-5 rounded-full bg-primary text-on-primary flex items-center justify-center">
                        <Check className="w-3 h-3 stroke-[3]" />
                      </div>
                    )}
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-on-surface">{lang.nativeName}</h3>
                    <p className="text-xs text-on-surface-variant font-medium">{lang.name}</p>
                    <span className="text-[10px] font-semibold text-primary block mt-1">
                      {lang.desc}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Intake Mode Cards */}
          <div className="mb-6">
            <label className="block text-xs font-bold text-on-surface mb-2">
              Clinical Intake Mode
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {/* Active Modern Medicine Card */}
              <div className="p-4 rounded-xl border-2 border-primary bg-secondary-container/10 flex items-start gap-3 shadow-xs">
                <div className="w-10 h-10 rounded-lg bg-primary text-on-primary flex items-center justify-center shrink-0">
                  <Stethoscope className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-1.5">
                    <h4 className="text-sm font-bold text-on-surface">Modern Medicine</h4>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-primary text-on-primary">
                      ACTIVE
                    </span>
                  </div>
                  <p className="text-xs text-on-surface-variant mt-1 leading-relaxed">
                    Standard allopathic clinical history covering chief complaint, HPI, medications, and surgical history.
                  </p>
                </div>
              </div>

              {/* Disabled AYUSH Card (Future Scope per Frozen MVP) */}
              <div className="p-4 rounded-xl border border-outline-variant/40 bg-surface-container-low/40 opacity-60 flex items-start gap-3 relative cursor-not-allowed">
                <div className="w-10 h-10 rounded-lg bg-surface-container flex items-center justify-center shrink-0 text-outline">
                  <Leaf className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-1.5">
                    <h4 className="text-sm font-bold text-on-surface">AYUSH Intake</h4>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-surface-container-high text-on-surface-variant">
                      PHASE 2
                    </span>
                  </div>
                  <p className="text-xs text-on-surface-variant mt-1 leading-relaxed">
                    Ayurvedic intake (Prakriti, Dosha, Nadi Pariksha) reserved for AYUSH hospital modules.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3 mt-auto pt-2">
            <button
              type="button"
              onClick={() => navigate('/consent')}
              className="flex-1 min-h-[48px] px-4 rounded-xl border border-outline-variant/60 text-on-surface font-semibold text-xs hover:bg-surface-container transition-colors flex items-center justify-center gap-1.5"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back</span>
            </button>

            <button
              type="button"
              onClick={handleStartSession}
              disabled={loading}
              className="flex-[2] min-h-[48px] px-6 rounded-xl bg-primary text-on-primary font-bold text-sm shadow-md hover:bg-primary-container transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
            >
              {loading ? (
                <span>Initializing AI Engine...</span>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Start AI Interview ({language})</span>
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

export default LanguagePage;
