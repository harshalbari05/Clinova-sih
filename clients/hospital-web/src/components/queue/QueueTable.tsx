import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Consultation } from '../../types/consultation';
import { StatusBadge, PriorityBadge } from '../common/Badge';
import { useOptionalAuth } from '../../context/AuthContext';

interface QueueTableProps {
  consultations: Consultation[];
  isLoading?: boolean;
  onSelectConsultation?: (consultation: Consultation) => void;
}

export const QueueTable: React.FC<QueueTableProps> = ({
  consultations,
  isLoading,
  onSelectConsultation,
}) => {
  const navigate = useNavigate();
  const auth = useOptionalAuth();
  const isReceptionist = auth?.hospitalRole === 'receptionist';

  if (isLoading) {
    return (
      <div className="bg-surface-container-lowest rounded-2xl border border-outline-variant/30 p-8 flex flex-col items-center justify-center gap-3">
        <div className="w-8 h-8 border-3 border-primary/20 border-t-primary rounded-full animate-spin" />
        <span className="text-xs text-on-surface-variant font-medium">Loading OPD Queue...</span>
      </div>
    );
  }

  if (consultations.length === 0) {
    return (
      <div className="bg-surface-container-lowest rounded-2xl border border-outline-variant/30 p-12 text-center flex flex-col items-center justify-center gap-3">
        <div className="w-12 h-12 rounded-full bg-secondary-container/60 text-secondary flex items-center justify-center">
          <span className="material-symbols-outlined text-[24px]">task_alt</span>
        </div>
        <div className="flex flex-col gap-1">
          <h3 className="text-base font-bold text-on-surface">No Patients in this Queue</h3>
          <p className="text-xs text-on-surface-variant max-w-sm">
            All consultations for this filter are currently completed or the queue is clear.
          </p>
        </div>
      </div>
    );
  }

  const formatTime = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return 'Today';
    }
  };

  return (
    <div className="bg-surface-container-lowest rounded-2xl border border-outline-variant/30 shadow-xs overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-on-surface min-w-[760px]">
          <thead className="bg-surface-container-low text-on-surface-variant text-xs font-semibold border-b border-outline-variant/20">
            <tr>
              <th scope="col" className="py-3.5 px-4 uppercase tracking-wider">
                Token / Patient
              </th>
              <th scope="col" className="py-3.5 px-4 uppercase tracking-wider">
                Chief Complaint
              </th>
              <th scope="col" className="py-3.5 px-4 uppercase tracking-wider">
                Check-in Time
              </th>
              <th scope="col" className="py-3.5 px-4 uppercase tracking-wider">
                Status
              </th>
              <th scope="col" className="py-3.5 px-4 uppercase tracking-wider">
                Triage / Priority
              </th>
              <th scope="col" className="py-3.5 px-4 text-right uppercase tracking-wider">
                Action
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-outline-variant/10 text-sm">
            {consultations.map((c, index) => {
              const tokenNum = c.token_number != null ? c.token_number : index + 1;
              const patientShortId = c.patient_id.slice(0, 8);

              return (
                <tr
                  key={c.id}
                  className={`hover:bg-surface-container-low/60 transition-colors group ${
                    isReceptionist ? 'cursor-default' : 'cursor-pointer'
                  }`}
                  onClick={() => {
                    if (!isReceptionist) {
                      if (onSelectConsultation) {
                        onSelectConsultation(c);
                      } else {
                        navigate(`/consultation/${c.id}`);
                      }
                    }
                  }}
                >
                  {/* Token & Patient Identifier */}
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-secondary-container text-on-secondary-container flex items-center justify-center font-black text-sm shrink-0 border border-primary/20">
                        #{tokenNum}
                      </div>
                      <div className="flex flex-col min-w-0">
                        <div className="flex items-center gap-1.5">
                          <span className="font-bold text-on-surface truncate group-hover:text-primary transition-colors">
                            Patient #{patientShortId}
                          </span>
                          {c.department && (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-primary/10 text-primary">
                              {c.department}
                            </span>
                          )}
                        </div>
                        <span className="text-[11px] text-on-surface-variant">
                          Case #{c.id.slice(0, 8)}
                        </span>
                      </div>
                    </div>
                  </td>

                  {/* Chief Complaint */}
                  <td className="py-4 px-4 max-w-[280px]">
                    <p className="text-xs text-on-surface font-medium truncate">
                      {c.chief_complaint || 'Self-reported intake pending or general checkup'}
                    </p>
                  </td>

                  {/* Time */}
                  <td className="py-4 px-4 whitespace-nowrap">
                    <span className="text-xs text-on-surface-variant flex items-center gap-1">
                      <span className="material-symbols-outlined text-[14px]">schedule</span>
                      {formatTime(c.created_at)}
                    </span>
                  </td>

                  {/* Status */}
                  <td className="py-4 px-4 whitespace-nowrap">
                    <StatusBadge status={c.status} />
                  </td>

                  {/* Priority / Triage */}
                  <td className="py-4 px-4 whitespace-nowrap">
                    <PriorityBadge urgency="NORMAL" />
                  </td>

                  {/* Action Button */}
                  <td className="py-4 px-4 text-right whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                    {isReceptionist ? (
                      <span className="px-2.5 py-1 rounded-lg bg-surface-container text-on-surface-variant text-xs font-semibold inline-flex items-center gap-1">
                        <span className="material-symbols-outlined text-[14px] text-primary">check</span>
                        <span>Registered</span>
                      </span>
                    ) : (
                      <button
                        onClick={() => (onSelectConsultation ? onSelectConsultation(c) : navigate(`/consultation/${c.id}`))}
                        className="px-3.5 py-1.5 rounded-xl bg-surface-container-high hover:bg-primary hover:text-on-primary text-on-surface font-semibold text-xs transition-colors shadow-xs inline-flex items-center gap-1.5"
                        type="button"
                      >
                        <span>Open Case</span>
                        <span className="material-symbols-outlined text-[15px]">arrow_forward</span>
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
