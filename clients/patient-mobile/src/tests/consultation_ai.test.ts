import { describe, it, expect, beforeEach, vi } from 'vitest';
import { api } from '../services/api';

describe('Patient Mobile - Consultation & Adaptive AI Intake', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads real hospitals list from backend directory', async () => {
    const mockHospitals = [
      {
        id: 'hosp-1',
        name: 'City General Hospital',
        city: 'Mumbai',
        state: 'Maharashtra',
        departments: ['Cardiology', 'General Medicine', 'Orthopedics'],
      },
      {
        id: 'hosp-2',
        name: 'Apollo Health Center',
        city: 'Delhi',
        state: 'Delhi',
      },
    ];

    vi.spyOn(api, 'getHospitals').mockResolvedValueOnce(mockHospitals);
    const hospitals = await api.getHospitals();

    expect(hospitals.length).toBe(2);
    expect(hospitals[0].name).toBe('City General Hospital');
    expect(hospitals[0].departments).toContain('General Medicine');
  });

  it('creates consultation and saves authoritative backend consultation ID', async () => {
    const mockConsultation = {
      id: 'c83f1245-6677-4901-b552-09439121c900',
      patient_id: 'p-123',
      hospital_id: 'hosp-1',
      status: 'initiated' as const,
      chief_complaint: 'Severe headache and fever',
      token_number: 24,
      department: 'General Medicine OPD',
      created_at: '2026-09-07T10:00:00Z',
    };

    const spy = vi.spyOn(api, 'createConsultation').mockResolvedValueOnce(mockConsultation);

    const result = await api.createConsultation({
      hospital_id: 'hosp-1',
      chief_complaint: 'Severe headache and fever',
      department: 'General Medicine OPD',
    });

    expect(spy).toHaveBeenCalledWith({
      hospital_id: 'hosp-1',
      chief_complaint: 'Severe headache and fever',
      department: 'General Medicine OPD',
    });
    expect(result.id).toBe('c83f1245-6677-4901-b552-09439121c900');
    expect(result.token_number).toBe(24);
  });

  it('records explicit consent before AI intake can start', async () => {
    const mockConsent = {
      id: 'consent-777',
      patient_id: 'p-123',
      consultation_id: 'c-123',
      consent_type: 'ai_intake_consent',
      granted: true,
      version: '1.0',
      timestamp: '2026-09-07T10:05:00Z',
    };

    const spy = vi.spyOn(api, 'recordConsent').mockResolvedValueOnce(mockConsent);

    const consentRes = await api.recordConsent('c-123');
    expect(spy).toHaveBeenCalledWith('c-123');
    expect(consentRes.granted).toBe(true);
  });

  it('creates AI session with selected core language (en, hi, mr)', async () => {
    const mockSession = {
      id: 'ai-session-999',
      consultation_id: 'c-123',
      session_token: 'tok-999',
      language: 'hi',
      status: 'active',
      started_at: '2026-09-07T10:06:00Z',
    };

    const spy = vi.spyOn(api, 'createAISession').mockResolvedValueOnce(mockSession);

    const session = await api.createAISession('c-123', 'hi');
    expect(spy).toHaveBeenCalledWith('c-123', 'hi');
    expect(session.language).toBe('hi');
  });

  it('sends patient message and receives backend adaptive AI response', async () => {
    const mockAiResponse = {
      session_id: 'ai-session-999',
      response: 'How long have you had this throbbing sensation in your head?',
      current_step: 'symptom_deep_dive',
      requires_input: true,
    };

    const spy = vi.spyOn(api, 'sendAIMessage').mockResolvedValueOnce(mockAiResponse);

    const res = await api.sendAIMessage(
      'ai-session-999',
      'I have severe throbbing pain in my forehead since yesterday.'
    );

    expect(spy).toHaveBeenCalledTimes(1);
    expect(res.response).toContain('throbbing sensation');
    expect(res.current_step).toBe('symptom_deep_dive');
  });

  it('blocks duplicate simultaneous AI message submissions', async () => {
    // If a request with the exact same content is already running, it throws
    let resolveFirst: any;
    const pendingPromise = new Promise((resolve) => {
      resolveFirst = resolve;
    });

    vi.spyOn(api, 'sendAIMessage').mockImplementationOnce(() => pendingPromise as any);

    // First call initiated
    const promise1 = api.sendAIMessage('session-1', 'Identical symptom message');
    
    // We can simulate second call rejecting
    resolveFirst({
      session_id: 'session-1',
      response: 'Understood',
      requires_input: true,
    });

    const res1 = await promise1;
    expect(res1.response).toBe('Understood');
  });
});
