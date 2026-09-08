import { aiApi } from '../api/ai';
import { triageApi } from '../api/triage';
import api from '../api/client';

jest.mock('../api/client');

describe('AI Clinical Interview & Triage Flow', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('creates an AI interview session passing the selected language', async () => {
    const mockSession = {
      id: 'sess-456',
      consultation_id: 'cons-123',
      session_token: 'tok-xyz',
      language: 'Hindi',
      status: 'in_progress',
      started_at: '2026-09-08T10:05:00Z',
    };

    (api.post as jest.Mock).mockResolvedValueOnce({ data: mockSession });

    const session = await aiApi.createSession('cons-123', 'Hindi');
    expect(api.post).toHaveBeenCalledWith('/consultations/cons-123/ai-sessions', {
      language: 'Hindi',
    });
    expect(session.id).toBe('sess-456');
    expect(session.language).toBe('Hindi');
  });

  it('sends patient answer to AI engine and retrieves follow-up interview question', async () => {
    const mockReply = {
      id: 'msg-2',
      session_id: 'sess-456',
      role: 'assistant',
      content: 'How long have you experienced chest discomfort?',
      step: 'symptom_exploration',
      is_complete: false,
    };

    (api.post as jest.Mock).mockResolvedValueOnce({ data: mockReply });

    const reply = await aiApi.sendMessage('sess-456', 'I have severe chest pain since yesterday');
    expect(api.post).toHaveBeenCalledWith('/ai-sessions/sess-456/messages', {
      content: 'I have severe chest pain since yesterday',
    });
    expect(reply.content).toContain('chest discomfort');
  });

  it('retrieves authoritative triage evaluation and identifies emergency red flag', async () => {
    const mockTriageResult = {
      id: 'tri-789',
      consultation_id: 'cons-123',
      priority: 'red',
      is_red_flag: true,
      requires_immediate_escalation: true,
      red_flags_detected: ['Acute chest pain with shortness of breath'],
      emergency_instructions: 'Proceed immediately to the emergency department or call an ambulance.',
    };

    (api.get as jest.Mock).mockResolvedValueOnce({ data: mockTriageResult });

    const result = await triageApi.getTriageResult('cons-123');
    expect(api.get).toHaveBeenCalledWith('/consultations/cons-123/triage');
    expect(result.priority).toBe('red');
    expect(result.is_red_flag).toBe(true);
    expect(result.requires_immediate_escalation).toBe(true);
  });
});
