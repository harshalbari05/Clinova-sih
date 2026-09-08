import { authApi } from '../api/auth';
import api from '../api/client';

jest.mock('../api/client');

describe('Patient Authentication Service', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('submits patient registration with correct payload schema', async () => {
    const mockPayload = {
      full_name: 'Aditi Verma',
      email: 'aditi@example.com',
      phone: '9876543210',
      password: 'password123',
      date_of_birth: '1995-08-20',
      gender: 'female',
    };

    const mockResponse = {
      user: { id: 'usr-1', email: 'aditi@example.com', phone: '9876543210', role: 'patient', is_active: true },
      account_type: 'patient',
      patient: { id: 'pat-1', user_id: 'usr-1', full_name: 'Aditi Verma' },
    };

    (api.post as jest.Mock).mockResolvedValueOnce({ data: mockResponse });

    const res = await authApi.register(mockPayload);
    expect(api.post).toHaveBeenCalledWith('/auth/patient/register', mockPayload);
    expect(res.account_type).toBe('patient');
    expect(res.patient?.full_name).toBe('Aditi Verma');
  });

  it('submits patient login and returns signed JWT token response', async () => {
    const loginPayload = {
      identifier: 'aditi@example.com',
      password: 'password123',
    };

    const mockTokenResponse = {
      access_token: 'mock-jwt-token-xyz',
      token_type: 'bearer',
      account_type: 'patient',
      user: { id: 'usr-1', email: 'aditi@example.com', role: 'patient', is_active: true },
      patient: { id: 'pat-1', user_id: 'usr-1', full_name: 'Aditi Verma' },
    };

    (api.post as jest.Mock).mockResolvedValueOnce({ data: mockTokenResponse });

    const res = await authApi.login(loginPayload);
    expect(api.post).toHaveBeenCalledWith('/auth/patient/login', loginPayload);
    expect(res.access_token).toBe('mock-jwt-token-xyz');
    expect(res.account_type).toBe('patient');
  });

  it('updates patient profile demographic details', async () => {
    const updatePayload = {
      full_name: 'Aditi Verma Updated',
      emergency_contact: '9876500000',
    };

    const mockUpdatedProfile = {
      id: 'pat-1',
      user_id: 'usr-1',
      full_name: 'Aditi Verma Updated',
      emergency_contact: '9876500000',
    };

    (api.put as jest.Mock).mockResolvedValueOnce({ data: mockUpdatedProfile });

    const res = await authApi.updatePatientProfile(updatePayload);
    expect(api.put).toHaveBeenCalledWith('/patients/me', updatePayload);
    expect(res.full_name).toBe('Aditi Verma Updated');
  });
});
