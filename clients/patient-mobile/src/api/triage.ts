import api from './client';
import { ClinicalAlert, TriageResult } from '../types';

export const triageApi = {
  async getTriageResult(consultationId: string): Promise<TriageResult> {
    const res = await api.get<TriageResult>(`/consultations/${consultationId}/triage`);
    return res.data;
  },

  async listAlerts(consultationId: string): Promise<{ items: ClinicalAlert[]; total: number }> {
    const res = await api.get<{ items: ClinicalAlert[]; total: number }>(
      `/consultations/${consultationId}/alerts`
    );
    return res.data;
  },
};

export default triageApi;
