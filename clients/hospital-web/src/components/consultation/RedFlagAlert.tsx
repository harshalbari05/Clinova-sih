import React from 'react';
import { TriageResult } from '../../types/triage';

interface RedFlagAlertProps {
  triage: TriageResult | null;
}

export const RedFlagAlert: React.FC<RedFlagAlertProps> = ({ triage }) => {
  if (!triage || (!triage.red_flags_detected && triage.urgency_level === 'NORMAL')) {
    return null;
  }

  const isEmergency = triage.urgency_level === 'EMERGENCY_REVIEW';

  return (
    <div className="rounded-2xl bg-error-container/30 border border-error/30 p-5 flex items-start gap-4 shadow-xs">
      <div className="w-10 h-10 rounded-xl bg-error text-on-error flex items-center justify-center shrink-0 mt-0.5">
        <span className="material-symbols-outlined text-[24px]">warning</span>
      </div>
      <div className="flex flex-col flex-1 min-w-0">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <span className="text-xs font-bold text-error uppercase tracking-wider">
            {isEmergency ? 'Emergency Clinical Review Required' : 'Potential Clinical Alert'}
          </span>
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-surface-container-lowest text-on-surface-variant text-[11px] font-medium border border-outline-variant/30">
            <span className="material-symbols-outlined text-[13px] text-primary">auto_awesome</span>
            AI-generated finding — Doctor review required
          </span>
        </div>

        <p className="text-sm text-on-surface font-bold mt-1">
          Red-flag finding detected in patient pre-intake. Immediate physician clinical review required.
        </p>

        {triage.findings && triage.findings.length > 0 && (
          <div className="mt-2 flex flex-col gap-1.5">
            {triage.findings.map((f, idx) => (
              <div key={idx} className="bg-surface-container-lowest/80 rounded-lg p-2 text-xs border border-error/20">
                <span className="font-bold text-error">[{f.severity}] {f.category}: </span>
                <span className="text-on-surface">{f.clinical_rationale}</span>
              </div>
            ))}
          </div>
        )}

        <p className="text-[11px] text-on-surface-variant italic mt-2">
          Strictly requires physical examination and diagnostic evaluation by attending physician before diagnosis. No medical diagnosis or treatment plan has been made by the system.
        </p>
      </div>
    </div>
  );
};
