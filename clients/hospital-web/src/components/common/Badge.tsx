import React from 'react';

interface StatusBadgeProps {
  status: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const normalized = status.toLowerCase();

  if (normalized === 'initiated' || normalized === 'waiting') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-secondary-container text-on-secondary-container">
        <span className="w-1.5 h-1.5 rounded-full bg-secondary" />
        Initiated
      </span>
    );
  }

  if (normalized === 'in_progress') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-primary-fixed text-on-primary-fixed">
        <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
        In Consultation
      </span>
    );
  }

  if (normalized === 'completed' || normalized === 'reviewed' || normalized === 'confirmed') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-teal-50 text-teal-800 border border-teal-200">
        <span className="material-symbols-outlined text-[13px]">check</span>
        {normalized === 'reviewed' || normalized === 'confirmed' ? 'Reviewed' : 'Completed'}
      </span>
    );
  }

  if (normalized === 'rejected') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-error-container text-on-error-container">
        <span className="material-symbols-outlined text-[13px]">close</span>
        Rejected
      </span>
    );
  }

  return (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-surface-container-high text-on-surface-variant">
      {status}
    </span>
  );
};

interface PriorityBadgeProps {
  urgency?: string;
  hasRedFlags?: boolean;
}

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({ urgency, hasRedFlags }) => {
  if (urgency === 'EMERGENCY_REVIEW' || hasRedFlags) {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-error-container text-on-error-container border border-error/20">
        <span className="material-symbols-outlined text-[14px]">warning</span>
        Emergency Review
      </span>
    );
  }

  if (urgency === 'URGENT') {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200">
        <span className="material-symbols-outlined text-[14px]">priority_high</span>
        Urgent
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-surface-container text-on-surface-variant">
      Normal
    </span>
  );
};

interface VerificationBadgeProps {
  status: string;
}

export const VerificationBadge: React.FC<VerificationBadgeProps> = ({ status }) => {
  if (status === 'CLINICIAN_VERIFIED') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-semibold bg-primary-container/20 text-primary">
        <span className="material-symbols-outlined text-[12px]">verified</span>
        Clinician Verified
      </span>
    );
  }

  if (status === 'SOURCE_CONFIRMED') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-semibold bg-secondary-container/50 text-on-secondary-container">
        <span className="material-symbols-outlined text-[12px]">fact_check</span>
        Source Confirmed
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-surface-container text-on-surface-variant">
      Unverified
    </span>
  );
};
