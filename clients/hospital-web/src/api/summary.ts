import { apiClient } from './client';
import { SummaryResponse, StructuredSummary } from '../types/summary';

export async function getSummary(consultationId: string): Promise<SummaryResponse> {
  const response = await apiClient.get<SummaryResponse>(`/consultations/${consultationId}/summary`);
  return response.data;
}

export async function generateSummary(consultationId: string, forceRebuild = false): Promise<SummaryResponse> {
  const response = await apiClient.post<SummaryResponse>(
    `/consultations/${consultationId}/summary/generate`,
    { force_rebuild: forceRebuild }
  );
  return response.data;
}

export interface SummaryEditPayload {
  summary_text?: string;
  structured_summary?: StructuredSummary;
  clinician_notes?: string;
}

export async function editSummary(consultationId: string, payload: SummaryEditPayload): Promise<SummaryResponse> {
  const response = await apiClient.put<SummaryResponse>(
    `/consultations/${consultationId}/summary`,
    payload
  );
  return response.data;
}

export interface SummaryConfirmPayload {
  clinician_notes?: string;
  confirm_timeline_events?: boolean;
}

export async function confirmSummary(consultationId: string, payload: SummaryConfirmPayload = {}): Promise<SummaryResponse> {
  const response = await apiClient.post<SummaryResponse>(
    `/consultations/${consultationId}/summary/confirm`,
    payload
  );
  return response.data;
}

export async function rejectSummary(consultationId: string, reason: string): Promise<SummaryResponse> {
  const response = await apiClient.post<SummaryResponse>(
    `/consultations/${consultationId}/summary/reject`,
    { reason }
  );
  return response.data;
}

export interface ReviewSummaryRequest {
  action: 'CONFIRMED' | 'REJECTED' | 'EDITED' | string;
  notes?: string;
  edited_summary?: string;
}

export async function reviewSummary(consultationId: string, payload: ReviewSummaryRequest): Promise<SummaryResponse> {
  if (payload.action === 'CONFIRMED') {
    return confirmSummary(consultationId, { clinician_notes: payload.notes });
  } else if (payload.action === 'REJECTED') {
    return rejectSummary(consultationId, payload.notes || 'Physician rejected draft');
  } else {
    return editSummary(consultationId, {
      summary_text: payload.edited_summary,
      clinician_notes: payload.notes,
    });
  }
}
