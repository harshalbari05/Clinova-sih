import api from './client';
import { TriageResult } from '../types';

export const triageApi = {
  async getTriageResult(consultationId: string): Promise<TriageResult> {
    const res = await api.get<TriageResult>(`/consultations/${consultationId}/triage`);
    return res.data;
  },
};
