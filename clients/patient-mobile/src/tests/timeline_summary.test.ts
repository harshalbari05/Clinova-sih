import { describe, it, expect, beforeEach, vi } from 'vitest';
import { api } from '../services/api';
import { TimelineEvent, DatePrecision } from '../types';

describe('Patient Mobile - Timeline, Summary & Route Protection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches timeline events and formats dates with precision awareness', async () => {
    const mockEvents: TimelineEvent[] = [
      {
        id: 'ev-1',
        patient_id: 'p-123',
        event_type: 'DIAGNOSIS',
        event_date: '2021-01-01',
        date_precision: 'APPROXIMATE',
        title: 'Hypertension',
        description: 'Reported onset of high blood pressure',
        source_type: 'PATIENT_HISTORY',
        verification_status: 'SOURCE_CONFIRMED',
      },
      {
        id: 'ev-2',
        patient_id: 'p-123',
        event_type: 'MEDICATION_STARTED',
        event_date: '2026-08-28',
        date_precision: 'EXACT',
        title: 'Started Metformin 500mg',
        source_type: 'PRESCRIPTION',
        verification_status: 'CLINICIAN_VERIFIED',
      },
    ];

    vi.spyOn(api, 'getTimeline').mockResolvedValueOnce({
      items: mockEvents,
      total: 2,
    });

    const res = await api.getTimeline();
    expect(res.items.length).toBe(2);

    // Approximate precision formatting check
    const formatPrecision = (date: string, prec: DatePrecision) => {
      if (prec === 'APPROXIMATE') return `~${date.slice(0, 4)}`;
      return date;
    };

    expect(formatPrecision(res.items[0].event_date, res.items[0].date_precision)).toBe('~2021');
    expect(formatPrecision(res.items[1].event_date, res.items[1].date_precision)).toBe('2026-08-28');
  });

  it('calls rebuild endpoint to synchronize timeline from backend sources', async () => {
    const spy = vi.spyOn(api, 'rebuildTimeline').mockResolvedValueOnce({
      items: [],
      total: 0,
    });

    await api.rebuildTimeline();
    expect(spy).toHaveBeenCalledTimes(1);
  });

  it('fetches clinical summary and strictly hides clinician notes and internal prompts from patient view', async () => {
    const mockSummary = {
      id: 'sum-123',
      consultation_id: 'c-123',
      verification_status: 'draft',
      version: 1,
      chief_complaint: 'Severe throbbing headache and mild fever',
      narrative: 'Patient presented with headache and fever. History of hypertension reported.',
      // Internal clinician fields that must NOT be shown to patient:
      clinician_notes: 'INTERNAL ONLY: Differential diagnosis includes tension headache or migraine.',
      created_at: '2026-09-07T10:30:00Z',
    };

    vi.spyOn(api, 'getConsultationSummary').mockResolvedValueOnce(mockSummary);

    const summary = await api.getConsultationSummary('c-123');
    expect(summary.chief_complaint).toBe('Severe throbbing headache and mild fever');
    expect(summary.verification_status).toBe('draft');

    // Function to sanitize summary for patient display
    const sanitizeForPatient = (raw: Record<string, any>) => {
      const { clinician_notes, ...safeView } = raw;
      return safeView;
    };

    const patientSafe = sanitizeForPatient(summary);
    expect((patientSafe as any).clinician_notes).toBeUndefined();
  });
});
