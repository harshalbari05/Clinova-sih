import api from './client';
import { Patient, ActiveVisit } from '../types';

export const patientApi = {
  async getProfile(): Promise<Patient> {
    const res = await api.get<Patient>('/patients/me');
    return res.data;
  },

  async updateProfile(payload: Partial<Patient>): Promise<Patient> {
    const res = await api.put<Patient>('/patients/me', payload);
    return res.data;
  },

  async getActiveVisit(): Promise<ActiveVisit> {
    const res = await api.get<ActiveVisit>('/patients/me/active-visit');
    return res.data;
  },
};

export default patientApi;
