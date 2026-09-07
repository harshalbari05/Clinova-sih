import { apiClient } from './client';
import { ClinicalHistoryResponse } from '../types/history';

export async function getClinicalHistory(consultationId: string): Promise<ClinicalHistoryResponse> {
  const response = await apiClient.get<ClinicalHistoryResponse>(
    `/consultations/${consultationId}/history`
  );
  return response.data;
}
