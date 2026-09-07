import api from './client';
import { ClinicalSummary } from '../types';

export const summaryApi = {
  async getSummary(consultationId: string): Promise<ClinicalSummary> {
    const res = await api.get<ClinicalSummary>(`/consultations/${consultationId}/summary`);
    return res.data;
  },

  async generateSummary(consultationId: string, forceRebuild = false): Promise<ClinicalSummary> {
    const res = await api.post<ClinicalSummary>(`/consultations/${consultationId}/summary/generate`, {
      force_rebuild: forceRebuild,
    });
    return res.data;
  },
};
