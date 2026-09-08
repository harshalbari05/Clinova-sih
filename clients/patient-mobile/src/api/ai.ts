import api from './client';
import { AIInterviewMessageResponse, AIMessage, AISession } from '../types';

export const aiApi = {
  async createSession(consultationId: string, language = 'English'): Promise<AISession> {
    const res = await api.post<AISession>(`/consultations/${consultationId}/ai-sessions`, {
      language,
    });
    return res.data;
  },

  async getSession(sessionId: string): Promise<AISession> {
    const res = await api.get<AISession>(`/ai-sessions/${sessionId}`);
    return res.data;
  },

  async completeSession(sessionId: string): Promise<AISession> {
    const res = await api.post<AISession>(`/ai-sessions/${sessionId}/complete`);
    return res.data;
  },

  async sendMessage(sessionId: string, content: string): Promise<AIInterviewMessageResponse> {
    const res = await api.post<AIInterviewMessageResponse>(`/ai-sessions/${sessionId}/messages`, {
      content,
    });
    return res.data;
  },

  async listMessages(sessionId: string, limit = 50, offset = 0): Promise<{ items: AIMessage[]; total: number }> {
    const res = await api.get<{ items: AIMessage[]; total: number }>(`/ai-sessions/${sessionId}/messages`, {
      params: { limit, offset },
    });
    return res.data;
  },
};

export default aiApi;
