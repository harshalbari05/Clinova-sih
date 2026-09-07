import api from './client';
import { TimelineEvent } from '../types';

export interface TimelineResponse {
  patient_id: string;
  total_events: number;
  events: TimelineEvent[];
}

export const timelineApi = {
  async getMyTimeline(order: 'asc' | 'desc' = 'asc'): Promise<TimelineResponse> {
    const res = await api.get<TimelineResponse>('/patients/me/timeline', {
      params: { order },
    });
    return res.data;
  },

  async rebuildTimeline(): Promise<TimelineResponse> {
    const res = await api.post<TimelineResponse>('/patients/me/timeline/rebuild');
    return res.data;
  },
};
