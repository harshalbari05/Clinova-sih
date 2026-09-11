import { hospitalApi } from '../api/hospitals';
import { consultationApi } from '../api/consultations';
import api from '../api/client';

jest.mock('../api/client');

describe('Hospital Directory & Consultation Services', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('lists public hospital directory safely without internal leak', async () => {
    const mockHospitals = [
      { id: 'hosp-1', name: 'AIIMS New Delhi', city: 'New Delhi', state: 'Delhi' },
      { id: 'hosp-2', name: 'Apollo Hospitals', city: 'Mumbai', state: 'Maharashtra' },
    ];

    (api.get as jest.Mock).mockResolvedValueOnce({ data: mockHospitals });

    const result = await hospitalApi.listHospitals();
    expect(api.get).toHaveBeenCalledWith('/hospitals');
    expect(result).toHaveLength(2);
    expect(result[0].name).toBe('AIIMS New Delhi');
    expect(result[0]).not.toHaveProperty('internal_credentials');
  });

  it('creates consultation for selected hospital', async () => {
    const mockConsultation = {
      id: 'cons-123',
      patient_id: 'pat-1',
      hospital_id: 'hosp-1',
      status: 'initiated',
      chief_complaint: 'Fever and severe cough',
      created_at: '2026-09-08T10:00:00Z',
    };

    (api.post as jest.Mock).mockResolvedValueOnce({ data: mockConsultation });

    const result = await consultationApi.createConsultation({
      hospital_id: 'hosp-1',
      chief_complaint: 'Fever and severe cough',
    });

    expect(api.post).toHaveBeenCalledWith('/consultations', {
      hospital_id: 'hosp-1',
      chief_complaint: 'Fever and severe cough',
    });
    expect(result.id).toBe('cons-123');
    expect(result.status).toBe('initiated');
  });

  it('records explicit informed consent on backend endpoint', async () => {
    const mockConsent = {
      id: 'consent-abc',
      patient_id: 'pat-1',
      consultation_id: 'cons-123',
      consent_type: 'clinical_intake',
      granted: true,
      version: '1.0',
      timestamp: '2026-09-08T10:01:00Z',
    };

    (api.post as jest.Mock).mockResolvedValueOnce({ data: mockConsent });

    const result = await consultationApi.recordConsent('cons-123', {
      consent_given: true,
      consent_type: 'clinical_intake',
    });

    expect(api.post).toHaveBeenCalledWith('/consultations/cons-123/consent', {
      consent_given: true,
      consent_type: 'clinical_intake',
    });
    expect(result.granted).toBe(true);
    expect(result.consent_type).toBe('clinical_intake');
  });

  it('retrieves active hospital visit and token for patient', async () => {
    const mockVisit = {
      has_active_visit: true,
      consultation_id: 'cons-123',
      hospital_id: 'hosp-1',
      hospital_name: 'Clinova General Hospital',
      department: 'General Medicine',
      token_number: 27,
      now_serving: 24,
      people_ahead: 2,
      status: 'waiting',
      checkin_time: '2026-09-11T10:00:00Z',
    };

    const { patientApi } = require('../api/patients');
    (api.get as jest.Mock).mockResolvedValueOnce({ data: mockVisit });

    const result = await patientApi.getActiveVisit();
    expect(api.get).toHaveBeenCalledWith('/patients/me/active-visit');
    expect(result.has_active_visit).toBe(true);
    expect(result.token_number).toBe(27);
    expect(result.department).toBe('General Medicine');
    expect(result.now_serving).toBe(24);
    expect(result.people_ahead).toBe(2);
  });
});

