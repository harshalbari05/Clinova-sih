import React, { useState } from 'react';
import { SummaryResponse } from '../../types/summary';
import { StatusBadge } from '../common/Badge';
import { SummaryEditModal } from './SummaryEditModal';
import { SummaryConfirmModal } from './SummaryConfirmModal';
import { SummaryRejectModal } from './SummaryRejectModal';

interface SummaryTabProps {
  summary: SummaryResponse | null;
  isLoading: boolean;
  onEdit: (text: string, notes: string) => Promise<void>;
  onConfirm: (notes?: string) => Promise<void>;
  onReject: (reason: string) => Promise<void>;
  onRegenerate: () => Promise<void>;
}

export const SummaryTab: React.FC<SummaryTabProps> = ({
  summary,
  isLoading,
  onEdit,
  onConfirm,
  onReject,
  onRegenerate,
}) => {
  const [showEdit, setShowEdit] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [showReject, setShowReject] = useState(false);
  const [isActionRunning, setIsActionRunning] = useState(false);

  if (isLoading) {
    return (
      <div className="p-8 flex flex-col items-center justify-center gap-3">
        <div className="w-8 h-8 border-3 border-primary/20 border-t-primary rounded-full animate-spin" />
        <span className="text-xs text-on-surface-variant font-medium">Assembling clinical summary...</span>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="bg-surface-container-lowest rounded-2xl p-8 border border-outline-variant/30 text-center flex flex-col items-center gap-3">
        <div className="w-12 h-12 rounded-full bg-secondary-container/50 text-secondary flex items-center justify-center">
          <span className="material-symbols-outlined text-[24px]">summarize</span>
        </div>
        <h3 className="text-base font-bold text-on-surface">No Clinical Summary Generated</h3>
        <p className="text-xs text-on-surface-variant max-w-sm">
          A pre-consultation summary draft has not been synthesized for this case yet.
        </p>
        <button
          onClick={onRegenerate}
          className="px-4 py-2 bg-primary hover:bg-primary-container text-on-primary text-xs font-bold rounded-xl transition-colors inline-flex items-center gap-1.5 mt-2"
          type="button"
        >
          <span className="material-symbols-outlined text-[16px]">auto_awesome</span>
          <span>Generate Summary Draft</span>
        </button>
      </div>
    );
  }

  const isConfirmed = summary.status === 'confirmed';
  const isRejected = summary.status === 'rejected';
  const structured = summary.structured_summary;

  const handleEditSave = async (text: string, notes: string) => {
    setIsActionRunning(true);
    try {
      await onEdit(text, notes);
    } finally {
      setIsActionRunning(false);
    }
  };

  const handleConfirmSubmit = async (notes?: string) => {
    setIsActionRunning(true);
    try {
      await onConfirm(notes);
    } finally {
      setIsActionRunning(false);
    }
  };

  const handleRejectSubmit = async (reason: string) => {
    setIsActionRunning(true);
    try {
      await onReject(reason);
    } finally {
      setIsActionRunning(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Summary Top Action Bar */}
      <div className="bg-surface-container-lowest rounded-2xl p-5 border border-outline-variant/30 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-[22px]">auto_awesome</span>
            <h2 className="text-base font-bold text-on-surface">AI-Generated Clinical Summary</h2>
          </div>
          <StatusBadge status={summary.status} />
          <span className="text-xs text-on-surface-variant font-semibold px-2 py-0.5 rounded-md bg-surface-container">
            v{summary.version}
          </span>
          {summary.reviewed_at && (
            <span className="text-xs text-on-surface-variant">
              Reviewed: {new Date(summary.reviewed_at).toLocaleDateString()}
            </span>
          )}
        </div>

        {/* Action CTAs */}
        <div className="flex items-center gap-2 flex-wrap">
          {!isConfirmed && !isRejected && (
            <>
              <button
                type="button"
                onClick={() => setShowEdit(true)}
                className="px-3.5 py-2 rounded-xl bg-surface-container hover:bg-surface-container-high text-on-surface text-xs font-semibold transition-colors flex items-center gap-1.5"
              >
                <span className="material-symbols-outlined text-[16px]">edit</span>
                <span>Edit Draft</span>
              </button>
              <button
                type="button"
                onClick={() => setShowReject(true)}
                className="px-3.5 py-2 rounded-xl text-error hover:bg-error-container/40 text-xs font-semibold transition-colors flex items-center gap-1.5"
              >
                <span className="material-symbols-outlined text-[16px]">cancel</span>
                <span>Reject</span>
              </button>
              <button
                type="button"
                onClick={() => setShowConfirm(true)}
                className="px-4 py-2 rounded-xl bg-primary hover:bg-primary-container text-on-primary text-xs font-bold transition-colors flex items-center gap-1.5 shadow-xs"
              >
                <span className="material-symbols-outlined text-[16px]">check_circle</span>
                <span>Confirm & Sign-off</span>
              </button>
            </>
          )}

          {isConfirmed && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-teal-50 text-teal-800 border border-teal-200 text-xs font-bold">
              <span className="material-symbols-outlined text-[16px]">verified</span>
              <span>Finalized by Clinician</span>
            </div>
          )}

          {isRejected && (
            <button
              type="button"
              onClick={onRegenerate}
              className="px-4 py-2 rounded-xl bg-primary hover:bg-primary-container text-on-primary text-xs font-bold transition-colors flex items-center gap-1.5"
            >
              <span className="material-symbols-outlined text-[16px]">refresh</span>
              <span>Regenerate Draft</span>
            </button>
          )}
        </div>
      </div>

      {/* Safety Disclaimer Banner */}
      <div className="bg-surface-container-low rounded-xl p-4 flex items-start gap-3 border border-outline-variant/20">
        <span className="material-symbols-outlined text-primary text-[20px] shrink-0 mt-0.5">
          verified_user
        </span>
        <div className="flex flex-col text-xs leading-relaxed text-on-surface-variant">
          <strong className="text-on-surface font-semibold">Assistive Intelligence Notice:</strong>
          <span>
            This clinical summary is an assistive pre-consultation draft. The attending physician remains solely responsible for history verification, physical examination, clinical diagnosis, and all treatment directives.
          </span>
        </div>
      </div>

      {/* Rejection notice if rejected */}
      {isRejected && summary.rejection_reason && (
        <div className="bg-error-container/30 border border-error-container p-4 rounded-xl flex items-start gap-3">
          <span className="material-symbols-outlined text-error text-[20px] shrink-0">block</span>
          <div className="flex flex-col text-xs">
            <span className="font-bold text-error">Draft Rejected by Clinician</span>
            <p className="text-on-surface mt-0.5">Reason: {summary.rejection_reason}</p>
          </div>
        </div>
      )}

      {/* Main Narrative Card */}
      <div className="bg-surface-container-lowest rounded-2xl p-6 border border-outline-variant/30 shadow-xs flex flex-col gap-3">
        <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
          Summary Narrative
        </span>
        <p className="text-sm font-medium text-on-surface leading-relaxed whitespace-pre-wrap">
          {summary.summary_text}
        </p>

        {summary.clinician_notes && (
          <div className="mt-4 pt-4 border-t border-outline-variant/20 flex flex-col gap-1 bg-surface-container-low/50 p-3 rounded-xl">
            <span className="text-[11px] font-bold text-primary uppercase tracking-wider">
              Clinician Internal Notes
            </span>
            <p className="text-xs text-on-surface font-medium">{summary.clinician_notes}</p>
          </div>
        )}
      </div>

      {/* Structured Clinical Findings with Provenance */}
      {structured && (
        <div className="flex flex-col gap-4">
          <h3 className="text-sm font-bold text-on-surface uppercase tracking-wider">
            Structured Findings & Provenance
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Symptoms */}
            <div className="bg-surface-container-lowest rounded-2xl p-5 border border-outline-variant/30 flex flex-col gap-2">
              <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[16px] text-primary">symptoms</span>
                Patient-Reported Symptoms
              </span>
              {structured.patient_reported_symptoms?.length > 0 ? (
                <div className="flex flex-col gap-1.5 mt-1">
                  {structured.patient_reported_symptoms.map((s, i) => (
                    <div key={i} className="p-2 rounded-lg bg-surface-container-low text-xs flex flex-col gap-0.5">
                      <span className="font-semibold text-on-surface">{s.item}</span>
                      {s.evidence && (
                        <span className="text-[11px] text-on-surface-variant italic">“{s.evidence}”</span>
                      )}
                      <span className="text-[10px] text-outline font-medium">Source: {s.source_type}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <span className="text-xs text-on-surface-variant italic">None reported</span>
              )}
            </div>

            {/* Current Medications */}
            <div className="bg-surface-container-lowest rounded-2xl p-5 border border-outline-variant/30 flex flex-col gap-2">
              <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[16px] text-primary">medication</span>
                Current Medications
              </span>
              {structured.current_medications?.length > 0 ? (
                <div className="flex flex-col gap-1.5 mt-1">
                  {structured.current_medications.map((m, i) => (
                    <div key={i} className="p-2 rounded-lg bg-surface-container-low text-xs flex flex-col gap-0.5">
                      <span className="font-semibold text-on-surface">{m.name}</span>
                      {(m.dosage || m.frequency) && (
                        <span className="text-[11px] text-on-surface-variant">
                          {[m.dosage, m.frequency].filter(Boolean).join(' • ')}
                        </span>
                      )}
                      <span className="text-[10px] text-outline font-medium">Source: {m.source_type}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <span className="text-xs text-on-surface-variant italic">No current medications reported</span>
              )}
            </div>

            {/* Past Medical & Surgical */}
            <div className="bg-surface-container-lowest rounded-2xl p-5 border border-outline-variant/30 flex flex-col gap-2">
              <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[16px] text-primary">history_edu</span>
                Past Medical & Surgical History
              </span>
              <div className="flex flex-col gap-1.5 mt-1">
                {structured.past_medical_history?.map((h, i) => (
                  <div key={`m-${i}`} className="p-2 rounded-lg bg-surface-container-low text-xs">
                    <span className="font-semibold text-on-surface">{h.item}</span>
                  </div>
                ))}
                {structured.past_surgical_history?.map((s, i) => (
                  <div key={`s-${i}`} className="p-2 rounded-lg bg-surface-container-low text-xs">
                    <span className="font-semibold text-on-surface">Surgery: {s.item}</span>
                  </div>
                ))}
                {(!structured.past_medical_history?.length && !structured.past_surgical_history?.length) && (
                  <span className="text-xs text-on-surface-variant italic">No prior conditions or surgeries</span>
                )}
              </div>
            </div>

            {/* Allergies */}
            <div className="bg-surface-container-lowest rounded-2xl p-5 border border-outline-variant/30 flex flex-col gap-2">
              <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[16px] text-primary">shield</span>
                Allergies
              </span>
              {structured.allergies?.length > 0 ? (
                <div className="flex flex-col gap-1.5 mt-1">
                  {structured.allergies.map((a, i) => (
                    <div key={i} className="p-2 rounded-lg bg-error-container/30 border border-error/20 text-xs">
                      <span className="font-bold text-error">{a.allergen}</span>
                      {a.reaction && <span className="text-on-surface"> — {a.reaction}</span>}
                    </div>
                  ))}
                </div>
              ) : (
                <span className="text-xs text-on-surface-variant italic">No documented allergies</span>
              )}
            </div>

            {/* Investigations / Labs */}
            {structured.relevant_investigations && structured.relevant_investigations.length > 0 && (
              <div className="md:col-span-2 bg-surface-container-lowest rounded-2xl p-5 border border-outline-variant/30 flex flex-col gap-2">
                <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-[16px] text-primary">lab_profile</span>
                  Relevant Lab Investigations (OCR / Reports)
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 mt-1">
                  {structured.relevant_investigations.map((inv, i) => (
                    <div key={i} className="p-2.5 rounded-xl bg-surface-container-low text-xs flex flex-col gap-1 border border-outline-variant/20">
                      <span className="font-semibold text-on-surface">{inv.test_name}</span>
                      <div className="flex items-baseline gap-1.5">
                        <span className="text-sm font-bold text-primary">{inv.result_value}</span>
                        {inv.unit && <span className="text-on-surface-variant">{inv.unit}</span>}
                        {inv.flag && (
                          <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${inv.flag.toLowerCase() === 'high' ? 'bg-error text-on-error' : 'bg-secondary text-on-secondary'}`}>
                            {inv.flag}
                          </span>
                        )}
                      </div>
                      {inv.source_document && (
                        <span className="text-[10px] text-outline truncate">Doc: {inv.source_document}</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Modals */}
      <SummaryEditModal
        isOpen={showEdit}
        onClose={() => setShowEdit(false)}
        summary={summary}
        onSave={handleEditSave}
        isSaving={isActionRunning}
      />

      <SummaryConfirmModal
        isOpen={showConfirm}
        onClose={() => setShowConfirm(false)}
        onConfirm={handleConfirmSubmit}
        isConfirming={isActionRunning}
      />

      <SummaryRejectModal
        isOpen={showReject}
        onClose={() => setShowReject(false)}
        onReject={handleRejectSubmit}
        isRejecting={isActionRunning}
      />
    </div>
  );
};
