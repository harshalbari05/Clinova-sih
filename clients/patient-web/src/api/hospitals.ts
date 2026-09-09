import api from './client';
import { Hospital } from '../types';

export const hospitalApi = {
  async listHospitals(): Promise<Hospital[]> {
    const res = await api.get<Hospital[]>('/hospitals');
    return Array.isArray(res.data) ? res.data : (res.data as any)?.items || [];
  },
};
