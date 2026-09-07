import React from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import {
  ArrowRight,
  Sparkles,
  ShieldCheck,
  Languages,
  FileText,
  Clock,
  HeartPulse,
  ScanLine,
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col bg-surface text-on-surface">
      <Navbar />

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-primary/5 via-surface to-surface">
        <div className="max-w-4xl mx-auto text-center flex flex-col items-center">
          {/* Tagline Pill */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-bold uppercase tracking-wider mb-6">
            <Sparkles className="w-3.5 h-3.5" />
            AI-Assisted Pre-Consultation History Engine
          </div>

          {/* Main Headline */}
          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-black text-on-surface tracking-tight leading-[1.15] mb-6">
            Your Medical History,{' '}
            <span className="text-primary underline decoration-secondary-container decoration-4 underline-offset-8">
              Ready Before
            </span>{' '}
            You Enter the Clinic
          </h1>

          <p className="text-base sm:text-xl text-on-surface-variant max-w-2xl mx-auto leading-relaxed mb-8">
            Complete your clinical intake at the hospital kiosk in your language through voice or touch. Your doctor receives a structured, evidence-backed summary before examination begins.
          </p>

          {/* Primary Call to Action */}
          <div className="flex flex-col sm:flex-row items-center gap-4 w-full justify-center max-w-md">
            <button
              onClick={() => navigate('/identify')}
              className="w-full sm:w-auto min-h-[52px] px-8 py-3.5 rounded-xl bg-primary text-on-primary font-bold text-base shadow-md hover:bg-primary-container transition-all flex items-center justify-center gap-2 group cursor-pointer active:scale-98"
            >
              <span>Start Patient Intake</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>

            <button
              onClick={() => navigate('/identify')}
              className="w-full sm:w-auto min-h-[52px] px-6 py-3.5 rounded-xl bg-surface-container-lowest text-on-surface font-semibold text-sm border border-outline-variant/60 shadow-xs hover:bg-surface-container transition-colors flex items-center justify-center gap-2"
            >
              <span>Existing Patient Sign-In</span>
            </button>
          </div>
        </div>
      </section>

      {/* How it Works Stepper Strip */}
      <section className="py-12 px-4 sm:px-6 bg-surface-container-lowest border-y border-outline-variant/30">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-on-surface">How Clinova Works</h2>
            <p className="text-sm text-on-surface-variant mt-1">
              Five quick steps at the reception kiosk to streamline your OPD visit
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {[
              {
                num: '1',
                title: 'Identify',
                desc: 'Enter your mobile or ABHA ID to associate your hospital visit.',
                icon: <ShieldCheck className="w-5 h-5 text-primary" />,
              },
              {
                num: '2',
                title: 'Speak in Your Tongue',
                desc: 'Choose English, Hindi, or Marathi with voice speech-to-text.',
                icon: <Languages className="w-5 h-5 text-secondary" />,
              },
              {
                num: '3',
                title: 'Adaptive Intake',
                desc: 'AI asks relevant clinical questions tailored to your symptoms.',
                icon: <HeartPulse className="w-5 h-5 text-error" />,
              },
              {
                num: '4',
                title: 'Scan Old Records',
                desc: 'Instant OCR extracts prescriptions and lab tests into a medical timeline.',
                icon: <ScanLine className="w-5 h-5 text-tertiary" />,
              },
              {
                num: '5',
                title: 'Doctor Summary',
                desc: 'A non-diagnostic summary is handed to your OPD physician.',
                icon: <FileText className="w-5 h-5 text-primary" />,
              },
            ].map((step) => (
              <div
                key={step.num}
                className="p-4 rounded-xl bg-surface-container-low/60 border border-outline-variant/20 flex flex-col items-start gap-2"
              >
                <div className="w-8 h-8 rounded-lg bg-surface-container-lowest flex items-center justify-center font-bold text-xs text-primary shadow-xs">
                  {step.num}
                </div>
                <div className="mt-1">{step.icon}</div>
                <h3 className="text-sm font-bold text-on-surface">{step.title}</h3>
                <p className="text-xs text-on-surface-variant leading-relaxed">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Safety & Compliance Reassurance */}
      <section className="py-14 px-4 sm:px-6 bg-surface">
        <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-5 rounded-2xl bg-surface-container-lowest shadow-sm border border-outline-variant/30 flex flex-col gap-2">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-base text-on-surface">Physician-Supervised</h3>
            <p className="text-xs text-on-surface-variant leading-relaxed">
              AI synthesizes reported facts and document records. Only licensed medical professionals diagnose and prescribe.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-surface-container-lowest shadow-sm border border-outline-variant/30 flex flex-col gap-2">
            <div className="w-10 h-10 rounded-xl bg-secondary-container flex items-center justify-center text-secondary">
              <Clock className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-base text-on-surface">Saves 8-12 Minutes</h3>
            <p className="text-xs text-on-surface-variant leading-relaxed">
              Eliminates repetitive paperwork. Your doctor starts consultation with complete timeline context.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-surface-container-lowest shadow-sm border border-outline-variant/30 flex flex-col gap-2">
            <div className="w-10 h-10 rounded-xl bg-error-container flex items-center justify-center text-error">
              <HeartPulse className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-base text-on-surface">Red-Flag Safety Triage</h3>
            <p className="text-xs text-on-surface-variant leading-relaxed">
              Automatic escalation alerts hospital nursing staff immediately if emergency symptoms are detected.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto py-6 px-4 bg-surface-container-lowest border-t border-outline-variant/30 text-center text-xs text-on-surface-variant">
        <p>
          CLINOVA • Smart India Hackathon Prototype • AI assistance only, requires licensed physician review.
        </p>
      </footer>
    </div>
  );
};

export default LandingPage;
