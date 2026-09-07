import React, { useState, useEffect } from 'react';
import { ClinicalHistoryResponse } from '../../types/history';
import { getClinicalHistory } from '../../api/history';

interface HistoryTabProps {
  consultationId?: string;
  history?: ClinicalHistoryResponse | null;
  isLoading?: boolean;
}

export const HistoryTab: React.FC<HistoryTabProps> = ({
  consultationId,
  history: propHistory,
  isLoading: propLoading = false,
}) => {
  const [history, setHistory] = useState<ClinicalHistoryResponse | null>(propHistory || null);
  const [loading, setLoading] = useState<boolean>(propLoading);

  useEffect(() => {
    if (propHistory !== undefined) {
      setHistory(propHistory);
      return;
    }
    if (consultationId) {
      setLoading(true);
      getClinicalHistory(consultationId)
        .then((res) => setHistory(res))
        .catch(() => setHistory(null))
        .finally(() => setLoading(false));
    }
  }, [consultationId, propHistory]);

  const isLoading = propLoading || loading;

  if (isLoading) {
    return (
      <div className="p-8 flex flex-col items-center justify-center gap-3">
        <div className="w-8 h-8 border-3 border-primary/20 border-t-primary rounded-full animate-spin" />
        <span className="text-xs text-on-surface-variant font-medium">Loading clinical intake record...</span>
      </div>
    );
  }

  const sections = [
    {
      title: 'Chief Complaint',
      icon: 'chat_bubble_outline',
      value: history?.chief_complaint,
      placeholder: 'No chief complaint recorded during pre-intake.',
    },
    {
      title: 'History of Present Illness (HPI)',
      icon: 'notes',
      value: history?.history_of_present_illness,
      placeholder: 'No history of present illness recorded.',
    },
    {
      title: 'Past Medical History',
      icon: 'medical_services',
      value: history?.past_medical_history,
      placeholder: 'No known chronic medical conditions reported.',
    },
    {
      title: 'Past Surgical History',
      icon: 'emergency',
      value: history?.past_surgical_history,
      placeholder: 'No surgical procedures or operations reported.',
    },
    {
      title: 'Drug & Medication History',
      icon: 'medication',
      value: history?.drug_history,
      placeholder: 'No current or past medications recorded.',
    },
    {
      title: 'Allergies & Adverse Reactions',
      icon: 'shield',
      value: history?.allergy_history,
      placeholder: 'No known drug or environmental allergies reported.',
    },
    {
      title: 'Family History',
      icon: 'family_restroom',
      value: history?.family_history,
      placeholder: 'No family medical history recorded.',
    },
    {
      title: 'Personal & Social History',
      icon: 'person',
      value: history?.personal_history,
      placeholder: 'No personal habits, dietary, or occupational details recorded.',
    },
    {
      title: 'Review of Systems (ROS)',
      icon: 'checklist',
      value: history?.review_of_systems,
      placeholder: 'Systemic review negative / unrecorded.',
    },
  ];

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-primary text-[22px]">history_edu</span>
          <h2 className="text-base font-bold text-on-surface">Structured Clinical Intake History</h2>
        </div>
        <span className="text-xs text-on-surface-variant">Self-reported by patient during intake</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sections.map((sec, idx) => (
          <div
            key={idx}
            className={`bg-surface-container-lowest rounded-2xl p-5 border border-outline-variant/30 shadow-xs flex flex-col gap-2 ${
              idx === 0 || idx === 1 ? 'md:col-span-2' : ''
            }`}
          >
            <div className="flex items-center gap-2 text-primary font-bold text-xs uppercase tracking-wider">
              <span className="material-symbols-outlined text-[18px]">{sec.icon}</span>
              <span>{sec.title}</span>
            </div>
            {sec.value ? (
              <p className="text-sm text-on-surface font-medium leading-relaxed mt-1">
                {sec.value}
              </p>
            ) : (
              <p className="text-xs text-on-surface-variant italic mt-1">
                {sec.placeholder}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
