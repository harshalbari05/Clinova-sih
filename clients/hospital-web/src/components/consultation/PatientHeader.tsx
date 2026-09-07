import React from 'react';
import { Consultation } from '../../types/consultation';
import { StatusBadge } from '../common/Badge';
import { Link } from 'react-router-dom';

interface PatientHeaderProps {
  consultation: Consultation;
  tokenNumber?: number;
}

export const PatientHeader: React.FC<PatientHeaderProps> = ({
  consultation,
  tokenNumber = 1,
}) => {
  const patientShort = consultation.patient_id.slice(0, 8);
  const initials = `P${patientShort.slice(0, 1).toUpperCase()}`;

  return (
    <div className="flex flex-col gap-4">
      {/* Back link */}
      <div className="flex items-center justify-between">
        <Link
          to="/queue"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-primary hover:text-primary-container transition-colors group"
        >
          <span className="material-symbols-outlined text-[18px] transition-transform group-hover:-translate-x-1">
            arrow_back
          </span>
          <span>Back to OPD Queue</span>
        </Link>
        <span className="text-xs text-on-surface-variant font-medium">
          Checked-in: {new Date(consultation.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>

      {/* Patient Banner Card */}
      <div className="bg-surface-container-lowest rounded-2xl p-6 border border-outline-variant/30 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-secondary-container text-on-secondary-container flex items-center justify-center font-bold text-xl shrink-0">
            {initials}
          </div>
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-xl font-bold text-on-surface tracking-tight">
                Patient #{patientShort}
              </h1>
              <StatusBadge status={consultation.status} />
            </div>
            <div className="flex items-center gap-x-3 gap-y-1 flex-wrap text-xs text-on-surface-variant">
              <span className="font-bold text-primary">Token #{tokenNumber}</span>
              <span className="text-outline-variant">•</span>
              <span>Case ID: <strong className="text-on-surface">#{consultation.id.slice(0, 8)}</strong></span>
              <span className="text-outline-variant">•</span>
              <span>Hospital Facility: OPD Room 104</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 self-start md:self-auto shrink-0">
          <div className="bg-surface-container-low rounded-xl px-4 py-2 flex flex-col items-end">
            <span className="text-[10px] uppercase tracking-wider text-on-surface-variant font-bold">
              Consultation Room
            </span>
            <span className="text-xs font-bold text-on-surface">
              General Medicine • 104
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
