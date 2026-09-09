import api from './client';
import { AIMessage, AISession } from '../types';

export interface AISessionCreatePayload {
  language?: string;
}

export interface AIMessageCreatePayload {
  message: string;
}

export interface AIInterviewMessageResponse {
  id: string;
  session_id: string;
  role: 'patient' | 'assistant' | 'ai' | 'system';
  content: string;
  step?: string | null;
  current_step_label?: string | null;
  options?: string[];
  is_complete?: boolean;
  created_at?: string;
  patient_message?: any;
  ai_message?: any;
  interview?: any;
  clinical_history_updates?: any;
}

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
    try {
      const res = await api.post<AISession>(`/ai-sessions/${sessionId}/complete`);
      return res.data;
    } catch (err: any) {
      if (err.response?.status === 409) {
        return await aiApi.getSession(sessionId);
      }
      throw err;
    }
  },

  async sendMessage(sessionId: string, message: string): Promise<AIInterviewMessageResponse> {
    const res = await api.post<any>(`/ai-sessions/${sessionId}/messages`, {
      message,
    });
    const data = res.data;
    const aiMsg = data.ai_message;
    const interview = data.interview;
    return {
      ...data,
      id: aiMsg?.id || data.id,
      session_id: aiMsg?.ai_session_id || data.ai_session_id || sessionId,
      role: (aiMsg?.sender === 'ai' ? 'ai' : 'assistant') as 'ai',
      content: aiMsg?.message || interview?.next_question || data.content || data.message || '',
      step: interview?.current_section || data.step || null,
      current_step_label: interview?.current_section ? interview.current_section.replace(/_/g, ' ') : data.current_step_label || null,
      options: data.options || [],
      is_complete: interview?.interview_complete ?? data.is_complete ?? false,
      created_at: aiMsg?.created_at || data.created_at,
    };
  },

  async listMessages(sessionId: string, limit = 50, offset = 0): Promise<{ items: AIMessage[]; total: number }> {
    const res = await api.get<{ items: any[]; total: number }>(`/ai-sessions/${sessionId}/messages`, {
      params: { limit, offset },
    });
    const items = (res.data?.items || []).map((item: any) => ({
      id: item.id,
      session_id: item.ai_session_id || item.session_id || sessionId,
      role: item.role || (item.sender === 'ai' ? 'ai' : 'patient'),
      content: item.content || item.message || '',
      step: item.step || null,
      current_step_label: item.current_step_label || null,
      options: item.options || [],
      is_complete: item.is_complete || false,
      created_at: item.created_at,
    }));
    return { items, total: res.data?.total ?? items.length };
  },
};

export default aiApi;
