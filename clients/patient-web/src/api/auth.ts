import api from './client';
import { AuthResponse, Patient, User } from '../types';

export interface PatientRegisterPayload {
  email: string;
  password: string;
  full_name: string;
  phone?: string;
  date_of_birth?: string;
  gender?: string;
  abha_id?: string;
  address?: string;
  emergency_contact?: string;
}

export interface PatientLoginPayload {
  identifier: string; // email, phone, or abha_id
  password: string;
}

export const authApi = {
  async register(payload: PatientRegisterPayload): Promise<AuthResponse> {
    const res = await api.post<AuthResponse>('/auth/patient/register', payload);
    return res.data;
  },

  async login(payload: PatientLoginPayload): Promise<AuthResponse> {
    const res = await api.post<AuthResponse>('/auth/patient/login', payload);
    return res.data;
  },

  async getMe(): Promise<{ account_type: string; user: User; patient?: Patient }> {
    const res = await api.get('/auth/me');
    return res.data;
  },

  async getPatientProfile(): Promise<Patient> {
    const res = await api.get<Patient>('/patients/me');
    return res.data;
  },

  async updatePatientProfile(payload: Partial<Patient>): Promise<Patient> {
    const res = await api.put<Patient>('/patients/me', payload);
    return res.data;
  },
};
