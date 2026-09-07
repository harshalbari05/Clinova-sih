import { apiClient } from './client';
import { TriageResult, AlertListResponse } from '../types/triage';

export async function getTriage(consultationId: string): Promise<TriageResult> {
  const response = await apiClient.get<TriageResult>(`/consultations/${consultationId}/triage`);
  return response.data;
}

export const getTriageResult = getTriage;

export async function listAlerts(consultationId: string): Promise<AlertListResponse> {
  const response = await apiClient.get<AlertListResponse>(`/consultations/${consultationId}/alerts`);
  return response.data;
}
