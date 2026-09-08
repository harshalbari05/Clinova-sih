import { timelineApi } from '../api/timeline';
import { summaryApi } from '../api/summary';
import api from '../api/client';

jest.mock('../api/client');

describe('Medical Timeline & Clinical Summary Services', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('retrieves patient chronological timeline with verification status', async () => {
    const mockTimeline = {
      patient_id: 'pat-1',
      total_events: 2,
      events: [
        {
          id: 'ev-1',
          patient_id: 'pat-1',
          event_type: 'diagnosis',
          event_date: '2024-01-15',
          title: 'Type 2 Diabetes Diagnosed',
          verification_status: 'SOURCE_CONFIRMED',
          source_type: 'prescription',
        },
        {
          id: 'ev-2',
          patient_id: 'pat-1',
          event_type: 'symptom',
          event_date: '2026-09-07',
          title: 'Persistent Dry Cough',
          verification_status: 'UNVERIFIED',
          source_type: 'patient_statement',
        },
      ],
    };

    (api.get as jest.Mock).mockResolvedValueOnce({ data: mockTimeline });

    const result = await timelineApi.getMyTimeline('asc');
    expect(api.get).toHaveBeenCalledWith('/patients/me/timeline', {
      params: { order: 'asc' },
    });
    expect(result.events).toHaveLength(2);
    expect(result.events[0].verification_status).toBe('SOURCE_CONFIRMED');
    expect(result.events[1].verification_status).toBe('UNVERIFIED');
  });

  it('rebuilds medical timeline using backend sync endpoint', async () => {
    const mockRebuilt = {
      patient_id: 'pat-1',
      total_events: 3,
      events: [],
    };

    (api.post as jest.Mock).mockResolvedValueOnce({ data: mockRebuilt });

    const res = await timelineApi.rebuildTimeline();
    expect(api.post).toHaveBeenCalledWith('/patients/me/timeline/rebuild');
    expect(res.total_events).toBe(3);
  });

  it('retrieves clinical summary and distinguishes AI draft vs confirmed', async () => {
    const mockSummaryDraft = {
      id: 'sum-123',
      consultation_id: 'cons-123',
      verification_status: 'draft',
      chief_complaint: 'Fever and chest discomfort',
      history_of_present_illness: 'Patient has experienced productive cough for 3 days.',
      version: 1,
      created_at: '2026-09-08T10:15:00Z',
    };

    (api.get as jest.Mock).mockResolvedValueOnce({ data: mockSummaryDraft });

    const summary = await summaryApi.getSummary('cons-123');
    expect(api.get).toHaveBeenCalledWith('/consultations/cons-123/summary');
    expect(summary.verification_status).toBe('draft');
    expect(summary.chief_complaint).toBe('Fever and chest discomfort');
  });

  it('requests regeneration of draft pre-consultation summary', async () => {
    const mockRegenerated = {
      id: 'sum-123',
      consultation_id: 'cons-123',
      verification_status: 'draft',
      version: 2,
    };

    (api.post as jest.Mock).mockResolvedValueOnce({ data: mockRegenerated });

    const summary = await summaryApi.generateSummary('cons-123', true);
    expect(api.post).toHaveBeenCalledWith('/consultations/cons-123/summary/generate', {
      force_rebuild: true,
    });
    expect(summary.version).toBe(2);
  });
});
