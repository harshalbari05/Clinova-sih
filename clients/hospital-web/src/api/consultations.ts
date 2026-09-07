import { apiClient } from './client';
import { Consultation, ConsultationListResponse } from '../types/consultation';

export interface ListConsultationParams {
  status?: string;
  limit?: number;
  offset?: number;
}

export async function listConsultations(params?: ListConsultationParams): Promise<ConsultationListResponse> {
  const queryParams: Record<string, string | number> = {};
  if (params?.status && params.status !== 'all') {
    queryParams.status = params.status;
  }
  if (params?.limit) {
    queryParams.limit = params.limit;
  }
  if (params?.offset !== undefined) {
    queryParams.offset = params.offset;
  }

  const response = await apiClient.get<ConsultationListResponse>('/consultations', {
    params: queryParams,
  });
  return response.data;
}

export async function getConsultation(consultationId: string): Promise<Consultation> {
  const response = await apiClient.get<Consultation>(`/consultations/${consultationId}`);
  return response.data;
}
