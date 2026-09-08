import api from './client';
import { PatientTimelineResponse } from '../types';

export const timelineApi = {
  async getMyTimeline(order: 'asc' | 'desc' = 'asc'): Promise<PatientTimelineResponse> {
    const res = await api.get<PatientTimelineResponse>('/patients/me/timeline', {
      params: { order },
    });
    return res.data;
  },

  async rebuildTimeline(): Promise<PatientTimelineResponse> {
    const res = await api.post<PatientTimelineResponse>('/patients/me/timeline/rebuild');
    return res.data;
  },
};

export default timelineApi;
