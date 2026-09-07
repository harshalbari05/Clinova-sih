import api from './client';
import { ConsentRecord, Consultation, ConsultationListResponse } from '../types';

export interface ConsultationCreatePayload {
  hospital_id: string;
  chief_complaint?: string;
}

export interface ConsentRecordPayload {
  consent_given?: boolean;
  consent_type?: string;
}

export const consultationApi = {
  async createConsultation(payload: ConsultationCreatePayload): Promise<Consultation> {
    const res = await api.post<Consultation>('/consultations', payload);
    return res.data;
  },

  async listConsultations(status?: string, limit = 20, offset = 0): Promise<ConsultationListResponse> {
    const params: Record<string, any> = { limit, offset };
    if (status) params.status = status;
    const res = await api.get<ConsultationListResponse>('/consultations', { params });
    return res.data;
  },

  async getConsultation(consultationId: string): Promise<Consultation> {
    const res = await api.get<Consultation>(`/consultations/${consultationId}`);
    return res.data;
  },

  async recordConsent(
    consultationId: string,
    payload: ConsentRecordPayload = { consent_given: true, consent_type: 'clinical_intake' }
  ): Promise<ConsentRecord> {
    const res = await api.post<ConsentRecord>(`/consultations/${consultationId}/consent`, payload);
    return res.data;
  },
};
