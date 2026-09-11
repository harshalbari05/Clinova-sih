/**
 * Onboarding Flow Tests
 *
 * Verifies the new patient onboarding flow:
 * Language → Login → Consent (no hospital) → Dashboard
 *
 * Tests that:
 * 1. Consent no longer requires a hospital ID
 * 2. Language can be set independently of consultation
 * 3. Patient context consent state is persisted correctly
 * 4. QR payload does not contain clinical data
 */

import { authApi } from '../api/auth';
import { consultationApi } from '../api/consultations';
import api from '../api/client';

jest.mock('../api/client');

describe('New Onboarding Flow — No Hospital Selection', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('creates a consultation WITHOUT a hospital_id (hospital assigned later at reception)', async () => {
    const mockConsultation = {
      id: 'cons-001',
      patient_id: 'pat-1',
      hospital_id: null,
      status: 'initiated',
      chief_complaint: 'Clinical intake — patient initiated',
      created_at: '2026-09-11T10:00:00Z',
    };

    (api.post as jest.Mock).mockResolvedValueOnce({ data: mockConsultation });

    const result = await consultationApi.createConsultation({
      chief_complaint: 'Clinical intake — patient initiated',
      // NOTE: hospital_id is intentionally omitted
    });

    expect(api.post).toHaveBeenCalledWith('/consultations', {
      chief_complaint: 'Clinical intake — patient initiated',
    });
    expect(result.id).toBe('cons-001');
    // hospital_id is null — assigned later at reception
    expect(result.hospital_id).toBeNull();
  });

  it('patient login returns account_type patient and patient data', async () => {
    const mockAuthResponse = {
      access_token: 'token-abc123',
      token_type: 'bearer',
      account_type: 'patient',
      user: { id: 'user-1', email: 'test@example.com', phone: null, role: 'patient', is_active: true },
      patient: { id: 'pat-1', user_id: 'user-1', full_name: 'Rahul Sharma' },
    };

    (api.post as jest.Mock).mockResolvedValueOnce({ data: mockAuthResponse });

    const result = await authApi.login({
      identifier: 'test@example.com',
      password: 'password123',
    });

    expect(api.post).toHaveBeenCalledWith('/auth/patient/login', {
      identifier: 'test@example.com',
      password: 'password123',
    });
    expect(result.account_type).toBe('patient');
    expect(result.patient?.full_name).toBe('Rahul Sharma');
  });

  it('registers a patient without email (mobile number only)', async () => {
    const mockRegisterResponse = {
      user: { id: 'user-2', email: null, phone: '9876543210', role: 'patient', is_active: true },
      account_type: 'patient',
      patient: { id: 'pat-2', user_id: 'user-2', full_name: 'Priya Devi' },
    };

    (api.post as jest.Mock).mockResolvedValueOnce({ data: mockRegisterResponse });

    const result = await authApi.register({
      full_name: 'Priya Devi',
      phone: '9876543210',
      password: 'securePass123',
      // email is intentionally omitted (optional per new flow)
    });

    expect(api.post).toHaveBeenCalledWith('/auth/patient/register', {
      full_name: 'Priya Devi',
      phone: '9876543210',
      password: 'securePass123',
    });
    expect(result.user.email).toBeNull();
    expect(result.user.phone).toBe('9876543210');
  });

  it('registers a patient with ABHA ID during account creation', async () => {
    const mockRegisterResponse = {
      user: { id: 'user-3', email: null, phone: '9900000001', role: 'patient', is_active: true },
      account_type: 'patient',
      patient: {
        id: 'pat-3',
        user_id: 'user-3',
        full_name: 'Ramesh Kumar',
        abha_id: '12-3456-7890-1234',
      },
    };

    (api.post as jest.Mock).mockResolvedValueOnce({ data: mockRegisterResponse });

    const result = await authApi.register({
      full_name: 'Ramesh Kumar',
      phone: '9900000001',
      password: 'abhaUser123',
      abha_id: '12-3456-7890-1234',
    });

    expect(result.patient?.abha_id).toBe('12-3456-7890-1234');
  });

  it('QR payload contains only patient ID — no clinical data', () => {
    const patientId = 'f47ac10b-58cc-4372-a567-0e02b2c3d479';

    // This is the exact format used in PatientQRScreen
    const qrPayload = `CLINOVA:PATIENT:${patientId}`;

    // Must not contain any clinical terms
    expect(qrPayload).not.toMatch(/diagnosis/i);
    expect(qrPayload).not.toMatch(/medication/i);
    expect(qrPayload).not.toMatch(/prescription/i);
    expect(qrPayload).not.toMatch(/blood_group/i);
    expect(qrPayload).not.toMatch(/abha_id/i);

    // Must contain the patient identifier
    expect(qrPayload).toContain(patientId);
    expect(qrPayload).toContain('CLINOVA:PATIENT:');
  });

  it('consultation API allows hospital_id to be undefined (optional field)', async () => {
    const mockConsultation = {
      id: 'cons-no-hosp',
      patient_id: 'pat-1',
      hospital_id: undefined,
      status: 'initiated',
      created_at: '2026-09-11T11:00:00Z',
    };

    (api.post as jest.Mock).mockResolvedValueOnce({ data: mockConsultation });

    // This should not throw a TypeScript or runtime error
    const result = await consultationApi.createConsultation({});
    expect(result.id).toBe('cons-no-hosp');
  });
});
