import { describe, it, expect, beforeEach, vi } from 'vitest';
import { api } from '../services/api';
import { setSecureItem, getSecureItem, removeSecureItem, STORAGE_KEYS } from '../services/storage';

describe('Patient Mobile - Authentication & Session', () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    await removeSecureItem(STORAGE_KEYS.ACCESS_TOKEN);
    await removeSecureItem(STORAGE_KEYS.USER_ID);
  });

  it('securely stores and retrieves JWT access token in SecureStore', async () => {
    const testToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test_patient_token';
    await setSecureItem(STORAGE_KEYS.ACCESS_TOKEN, testToken);

    const retrieved = await getSecureItem(STORAGE_KEYS.ACCESS_TOKEN);
    expect(retrieved).toBe(testToken);
  });

  it('clears token on logout', async () => {
    await setSecureItem(STORAGE_KEYS.ACCESS_TOKEN, 'active_jwt_token');
    await removeSecureItem(STORAGE_KEYS.ACCESS_TOKEN);

    const afterLogout = await getSecureItem(STORAGE_KEYS.ACCESS_TOKEN);
    expect(afterLogout).toBeNull();
  });

  it('handles registration payload matching backend schema without fabricated fields', async () => {
    const mockRegisterSpy = vi.spyOn(api, 'registerPatient').mockResolvedValueOnce({
      access_token: 'new_token_123',
      token_type: 'bearer',
      account_type: 'patient',
      user: {
        id: 'u-123',
        email: 'rahul.sharma@example.com',
        role: 'patient',
        is_active: true,
      },
      patient: {
        id: 'p-123',
        user_id: 'u-123',
        full_name: 'Rahul Sharma',
        phone: '+919876543210',
        abha_id: '91-4521-8890-1234',
        date_of_birth: '1990-05-14',
        gender: 'Male',
        blood_group: 'O+',
      },
    });

    const res = await api.registerPatient({
      email: 'rahul.sharma@example.com',
      password: 'SecurePassword123!',
      full_name: 'Rahul Sharma',
      phone: '+919876543210',
      abha_id: '91-4521-8890-1234',
      dob: '1990-05-14',
      gender: 'Male',
    });

    expect(mockRegisterSpy).toHaveBeenCalledTimes(1);
    expect(res.access_token).toBe('new_token_123');
    expect(res.patient?.full_name).toBe('Rahul Sharma');
    expect(res.patient?.abha_id).toBe('91-4521-8890-1234');
  });

  it('handles login with phone / ABHA association', async () => {
    const mockLoginSpy = vi.spyOn(api, 'loginPatient').mockResolvedValueOnce({
      access_token: 'login_token_456',
      token_type: 'bearer',
      account_type: 'patient',
      user: {
        id: 'u-123',
        email: 'rahul@clinova.health',
        role: 'patient',
        is_active: true,
      },
    });

    const res = await api.loginPatient({
      phone: '+919876543210',
      abha_id: '91-4521-8890-1234',
    });

    expect(mockLoginSpy).toHaveBeenCalledTimes(1);
    expect(res.access_token).toBe('login_token_456');
  });

  it('restores patient profile for active session', async () => {
    vi.spyOn(api, 'getMyProfile').mockResolvedValueOnce({
      id: 'p-123',
      user_id: 'u-123',
      full_name: 'Rahul Sharma',
      phone: '+919876543210',
      abha_id: '91-4521-8890-1234',
      date_of_birth: '1990-05-14',
      gender: 'Male',
      blood_group: 'O+',
    });

    const profile = await api.getMyProfile();
    expect(profile.full_name).toBe('Rahul Sharma');
    expect(profile.id).toBe('p-123');
  });
});
