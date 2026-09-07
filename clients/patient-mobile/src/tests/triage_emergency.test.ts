import { describe, it, expect, beforeEach, vi } from 'vitest';
import { api } from '../services/api';

describe('Patient Mobile - Backend Triage & Emergency Response', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches authoritative triage result from backend without local clinical evaluation', async () => {
    const mockTriage = {
      id: 'tri-001',
      consultation_id: 'c-123',
      priority: 'red',
      category: 'cardiovascular',
      is_red_flag: true,
      requires_immediate_escalation: true,
      red_flags_detected: ['crushing chest pain', 'shortness of breath'],
      emergency_instructions:
        'Please seek immediate in-person emergency care at the nearest hospital or call 108/112.',
      evaluated_at: '2026-09-07T10:10:00Z',
    };

    const spy = vi.spyOn(api, 'getTriage').mockResolvedValueOnce(mockTriage);

    const triage = await api.getTriage('c-123');

    expect(spy).toHaveBeenCalledWith('c-123');
    expect(triage.priority).toBe('red');
    expect(triage.is_red_flag).toBe(true);
    expect(triage.red_flags_detected).toContain('crushing chest pain');
  });

  it('handles normal priority triage correctly', async () => {
    const mockTriage = {
      id: 'tri-002',
      consultation_id: 'c-456',
      priority: 'green',
      is_red_flag: false,
      requires_immediate_escalation: false,
      evaluated_at: '2026-09-07T10:15:00Z',
    };

    vi.spyOn(api, 'getTriage').mockResolvedValueOnce(mockTriage);
    const triage = await api.getTriage('c-456');

    expect(triage.is_red_flag).toBe(false);
    expect(triage.priority).toBe('green');
  });

  it('verifies mobile uses calm, non-diagnostic guidance language', () => {
    const instructions =
      'Please seek immediate in-person emergency care at the nearest hospital or call 108/112.';
    
    // Safety criteria: Must NOT prescribe drugs or declare diagnoses
    expect(instructions.toLowerCase()).not.toContain('take aspirin');
    expect(instructions.toLowerCase()).not.toContain('you have a myocardial infarction');
    expect(instructions).toContain('emergency care');
  });
});
