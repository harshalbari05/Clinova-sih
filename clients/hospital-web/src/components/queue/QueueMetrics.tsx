import React from 'react';

interface QueueMetricsProps {
  waitingCount?: number;
  inConsultationCount?: number;
  completedCount?: number;
  urgentCount?: number;
  total?: number;
  waiting?: number;
  inProgress?: number;
  completed?: number;
}

export const QueueMetrics: React.FC<QueueMetricsProps> = ({
  waitingCount,
  inConsultationCount,
  completedCount,
  urgentCount = 0,
  waiting,
  inProgress,
  completed,
}) => {
  const finalWaiting = waitingCount ?? waiting ?? 0;
  const finalInConsultation = inConsultationCount ?? inProgress ?? 0;
  const finalCompleted = completedCount ?? completed ?? 0;
  const finalUrgent = urgentCount;
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. Patients Waiting */}
      <div className="bg-surface-container-lowest p-5 rounded-2xl border border-outline-variant/30 shadow-xs flex flex-col justify-between min-h-[130px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
            Patients Waiting
          </span>
          <span className="material-symbols-outlined text-primary text-[24px]">groups</span>
        </div>
        <div>
          <div className="text-3xl font-bold text-on-surface leading-tight">{finalWaiting}</div>
          <p className="text-xs text-on-surface-variant mt-1">In OPD lounge (FIFO queue)</p>
        </div>
      </div>

      {/* 2. In Consultation */}
      <div className="bg-surface-container-lowest p-5 rounded-2xl border border-outline-variant/30 shadow-xs flex flex-col justify-between min-h-[130px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
            In Consultation
          </span>
          <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-secondary-container">
            <span className="w-2 h-2 rounded-full bg-secondary animate-ping" />
          </span>
        </div>
        <div>
          <div className="text-3xl font-bold text-on-surface leading-tight">{finalInConsultation}</div>
          <p className="text-xs text-on-surface-variant mt-1">Active in consultation rooms</p>
        </div>
      </div>

      {/* 3. Completed */}
      <div className="bg-surface-container-lowest p-5 rounded-2xl border border-outline-variant/30 shadow-xs flex flex-col justify-between min-h-[130px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
            Completed
          </span>
          <span className="material-symbols-outlined text-secondary text-[24px]">task_alt</span>
        </div>
        <div>
          <div className="text-3xl font-bold text-on-surface leading-tight">{finalCompleted}</div>
          <p className="text-xs text-on-surface-variant mt-1">Consultations reviewed / closed</p>
        </div>
      </div>

      {/* 4. Needs Attention */}
      <div className="bg-surface-container-lowest p-5 rounded-2xl border border-outline-variant/30 shadow-xs flex flex-col justify-between min-h-[130px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-error uppercase tracking-wider">
            Urgent Review
          </span>
          <span className="material-symbols-outlined text-error text-[24px]">warning</span>
        </div>
        <div>
          <div className="text-3xl font-bold text-error leading-tight">{finalUrgent}</div>
          <p className="text-xs text-on-surface-variant mt-1">Requires clinical desk priority</p>
        </div>
      </div>
    </div>
  );
};
