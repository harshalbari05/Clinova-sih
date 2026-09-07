import React from 'react';
import { AlertTriangle, Phone, ArrowRight, ShieldAlert } from 'lucide-react';
import { TriageResult } from '../types';

export interface EmergencyOverlayProps {
  triage?: TriageResult | null;
  triageResult?: TriageResult | null;
  onDismiss?: () => void;
  onAcknowledge?: () => void;
}

export const EmergencyOverlay: React.FC<EmergencyOverlayProps> = ({ 
  triage, 
  triageResult, 
  onDismiss, 
  onAcknowledge 
}) => {
  const activeTriage = triage || triageResult;
  const handleAcknowledge = onAcknowledge || onDismiss || (() => {});
  if (!activeTriage) return null;

  const isRed = activeTriage.priority?.toLowerCase() === 'red' || activeTriage.priority === 'EMERGENCY' || activeTriage.is_red_flag;
  const isEmergency = isRed || activeTriage.requires_immediate_escalation;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-900/80 backdrop-blur-md"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="triage-alert-title"
    >
      {/* Background Pulsing Rings */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none flex items-center justify-center">
        <div className="w-[300px] h-[300px] rounded-full border-2 border-error/20 animate-ping opacity-40" />
        <div className="w-[500px] h-[500px] rounded-full border-2 border-error/10 animate-pulse opacity-30" />
      </div>

      <div className="relative w-full max-w-lg bg-surface-container-lowest rounded-2xl border-2 border-error shadow-2xl p-6 sm:p-8 flex flex-col items-center text-center z-10 animate-in fade-in zoom-in duration-200">
        {/* Warning Icon with Pulsing Halo */}
        <div className="w-20 h-20 rounded-full bg-error-container/60 border-2 border-error flex items-center justify-center text-error mb-4 shadow-emergency">
          <AlertTriangle className="w-10 h-10 animate-bounce" />
        </div>

        {/* Priority Badge */}
        <div className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-error text-on-error font-bold text-xs uppercase tracking-wider mb-3">
          <ShieldAlert className="w-3.5 h-3.5" />
          {isEmergency ? 'Urgent Medical Attention Required' : 'Clinical Priority Alert'}
        </div>

        {/* Main Title */}
        <h2 id="triage-alert-title" className="text-xl sm:text-2xl font-black text-on-surface leading-tight mb-2">
          {isEmergency
            ? 'POTENTIAL EMERGENCY DETECTED'
            : 'CLINICAL ESCALATION RECOMMENDED'}
        </h2>

        {/* Disclaimer Card */}
        <div className="w-full bg-surface-container-low rounded-xl p-3.5 border border-outline-variant/40 mb-4 text-left">
          <p className="text-xs font-bold text-on-surface mb-1 flex items-center gap-1">
            <span>⚠️</span> AI Safety Guardrail Notification
          </p>
          <p className="text-xs text-on-surface-variant leading-relaxed">
            This AI assistant does not provide medical diagnoses. Your reported symptoms have triggered an immediate clinical safety alert that requires attending hospital staff review.
          </p>
        </div>

        {/* Alert Notes / Description */}
        {activeTriage.triage_notes && (
          <p className="text-xs font-semibold text-error mb-3 leading-relaxed">
            {activeTriage.triage_notes}
          </p>
        )}

        {/* Symptoms list */}
        {activeTriage.trigger_symptoms && activeTriage.trigger_symptoms.length > 0 && (
          <div className="w-full bg-error-container/30 border border-error/30 rounded-xl p-3 mb-4 text-left">
            <span className="text-[11px] font-bold text-error uppercase tracking-wider block mb-1">
              Symptoms Reported:
            </span>
            <div className="flex flex-wrap gap-1.5">
              {activeTriage.trigger_symptoms.map((sym, idx) => (
                <span
                  key={idx}
                  className="inline-block px-2.5 py-0.5 rounded-full bg-error text-on-error text-xs font-semibold"
                >
                  {sym}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Emergency Instructions */}
        {activeTriage.emergency_instructions && (
          <p className="text-sm font-semibold text-error mb-5 leading-relaxed">
            {activeTriage.emergency_instructions}
          </p>
        )}

        <p className="text-xs text-on-surface-variant mb-4">
          Please notify OPD nursing staff immediately to fast-track your priority consultation.
        </p>

        {/* Immediate Call Action */}
        <div className="w-full flex flex-col gap-2.5">
          <a
            href="tel:108"
            className="w-full py-3.5 px-4 rounded-xl bg-error text-on-error font-bold text-base shadow-lg hover:bg-error/90 transition-colors flex items-center justify-center gap-2"
          >
            <Phone className="w-5 h-5" />
            Alert Hospital Staff / Call 108 Emergency
          </a>

          {/* Dismiss / Acknowledge button */}
          <button
            type="button"
            onClick={handleAcknowledge}
            className="w-full py-2.5 px-4 rounded-xl border border-outline-variant/60 text-on-surface-variant font-semibold text-xs hover:bg-surface-container transition-colors flex items-center justify-center gap-1.5"
          >
            <span>I Have Notified Medical Staff</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default EmergencyOverlay;
