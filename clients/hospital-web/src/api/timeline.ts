import { apiClient } from './client';
import { PatientTimelineResponse } from '../types/timeline';

export interface TimelineFilterParams {
  event_type?: string;
  source_type?: string;
  order?: 'asc' | 'desc';
}

export async function getConsultationTimeline(
  consultationId: string,
  params?: TimelineFilterParams
): Promise<PatientTimelineResponse> {
  const queryParams: Record<string, string> = {};
  if (params?.event_type && params.event_type !== 'all') {
    queryParams.event_type = params.event_type;
  }
  if (params?.source_type && params.source_type !== 'all') {
    queryParams.source_type = params.source_type;
  }
  if (params?.order) {
    queryParams.order = params.order;
  }

  const response = await apiClient.get<PatientTimelineResponse>(
    `/consultations/${consultationId}/timeline`,
    { params: queryParams }
  );
  return response.data;
}
