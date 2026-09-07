import React, { useState, useEffect } from 'react';
import { TimelineEvent } from '../../types/timeline';
import { VerificationBadge } from '../common/Badge';
import { getConsultationTimeline } from '../../api/timeline';

interface TimelineTabProps {
  consultationId?: string;
  events?: TimelineEvent[];
  isLoading?: boolean;
}

export const TimelineTab: React.FC<TimelineTabProps> = ({
  consultationId,
  events: propEvents,
  isLoading: propLoading = false,
}) => {
  const [selectedType, setSelectedType] = useState('all');
  const [events, setEvents] = useState<TimelineEvent[]>(propEvents || []);
  const [loading, setLoading] = useState<boolean>(propLoading);

  useEffect(() => {
    if (propEvents !== undefined) {
      setEvents(propEvents);
      return;
    }
    if (consultationId) {
      setLoading(true);
      getConsultationTimeline(consultationId)
        .then((res) => setEvents(res.events || []))
        .catch(() => setEvents([]))
        .finally(() => setLoading(false));
    }
  }, [consultationId, propEvents]);

  const isLoading = propLoading || loading;

  if (isLoading) {
    return (
      <div className="p-8 flex flex-col items-center justify-center gap-3">
        <div className="w-8 h-8 border-3 border-primary/20 border-t-primary rounded-full animate-spin" />
        <span className="text-xs text-on-surface-variant font-medium">Assembling medical timeline...</span>
      </div>
    );
  }

  const filtered = selectedType === 'all'
    ? events
    : events.filter((e) => e.event_type.toLowerCase().includes(selectedType.toLowerCase()));

  const mapProvenance = (sourceType: string) => {
    switch (sourceType.toUpperCase()) {
      case 'PATIENT_HISTORY':
      case 'PATIENT_REPORTED':
        return 'Patient Reported Intake';
      case 'DOCUMENT_OCR':
      case 'OCR_DOCUMENT':
      case 'MEDICAL_DOCUMENT':
        return 'Medical Document OCR';
      case 'AI_INTERVIEW':
        return 'Intake Interview Turn';
      case 'CLINICIAN_ENTERED':
        return 'Clinician Verified';
      default:
        return sourceType;
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Header and Filter */}
      <div className="bg-surface-container-lowest rounded-2xl p-5 border border-outline-variant/30 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-primary text-[22px]">timeline</span>
          <div>
            <h2 className="text-base font-bold text-on-surface">Medical Timeline</h2>
            <span className="text-xs text-on-surface-variant">{events.length} chronological milestones</span>
          </div>
        </div>

        {/* Filter Chips */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 text-xs">
          {['all', 'symptom', 'medical', 'medication', 'lab'].map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setSelectedType(t)}
              className={`px-3 py-1.5 rounded-xl font-semibold capitalize transition-colors ${
                selectedType === t
                  ? 'bg-primary text-on-primary shadow-xs'
                  : 'bg-surface-container-low text-on-surface-variant hover:bg-surface-container'
              }`}
            >
              {t === 'all' ? 'All Events' : t}
            </button>
          ))}
        </div>
      </div>

      {/* Timeline List */}
      {filtered.length === 0 ? (
        <div className="bg-surface-container-lowest rounded-2xl p-8 border border-outline-variant/30 text-center flex flex-col items-center gap-2">
          <span className="material-symbols-outlined text-outline text-[32px]">event_busy</span>
          <p className="text-xs text-on-surface-variant">No timeline events match the selected criteria.</p>
        </div>
      ) : (
        <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-outline-variant/30">
          {filtered.map((ev) => (
            <div key={ev.id} className="relative group">
              {/* Dot on line */}
              <div className="absolute -left-[1.85rem] top-1.5 w-3.5 h-3.5 rounded-full bg-primary border-2 border-surface-container-lowest ring-2 ring-primary/20" />

              {/* Event Card */}
              <div className="bg-surface-container-lowest rounded-2xl p-5 border border-outline-variant/30 shadow-xs flex flex-col gap-2 hover:border-primary/40 transition-colors">
                <div className="flex items-center justify-between gap-3 flex-wrap">
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-secondary-container text-on-secondary-container">
                      {ev.event_type}
                    </span>
                    <span className="text-xs font-bold text-on-surface-variant">
                      {ev.event_date || 'Undated / Baseline'}
                    </span>
                  </div>
                  <VerificationBadge status={ev.verification_status} />
                </div>

                <h3 className="text-sm font-bold text-on-surface">{ev.title}</h3>

                {ev.description && (
                  <p className="text-xs text-on-surface-variant leading-relaxed">{ev.description}</p>
                )}

                {/* Provenance Footer */}
                <div className="mt-2 pt-2 border-t border-outline-variant/20 flex items-center justify-between gap-2 flex-wrap text-[11px] text-outline">
                  <span className="inline-flex items-center gap-1">
                    <span className="material-symbols-outlined text-[14px] text-primary">source</span>
                    Source: <strong className="text-on-surface-variant">{mapProvenance(ev.source_type)}</strong>
                  </span>
                  {ev.evidence && (
                    <span className="italic text-on-surface-variant truncate max-w-xs">
                      “{ev.evidence}”
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
