import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { PatientHeader } from '../components/consultation/PatientHeader';
import { RedFlagAlert } from '../components/consultation/RedFlagAlert';
import { SummaryTab } from '../components/consultation/SummaryTab';
import { Consultation } from '../types/consultation';
import { SummaryResponse } from '../types/summary';
import { TriageResult } from '../types/triage';

describe('Consultation Workspace Components', () => {
  const mockConsultation: Consultation = {
    id: 'consult-12345678-uuid',
    patient_id: 'patient-87654321-uuid',
    hospital_id: 'hospital-aiims-uuid',
    status: 'initiated',
    chief_complaint: 'Severe chest pain radiating to left shoulder',
    started_at: null,
    completed_at: null,
    created_at: '2026-09-07T08:00:00Z',
    updated_at: '2026-09-07T08:00:00Z',
  };

  it('renders PatientHeader with patient token and consultation case ID', () => {
    render(
      <BrowserRouter>
        <PatientHeader consultation={mockConsultation} tokenNumber={3} />
      </BrowserRouter>
    );

    expect(screen.getByText(/Patient #patient-/i)).toBeInTheDocument();
    expect(screen.getByText(/Token #3/i)).toBeInTheDocument();
    expect(screen.getByText(/#consult-/i)).toBeInTheDocument();
    expect(screen.getByText(/Back to OPD Queue/i)).toBeInTheDocument();
  });

  it('renders RedFlagAlert when emergency clinical findings are detected', () => {
    const mockTriage: TriageResult = {
      consultation_id: 'consult-123',
      urgency_level: 'EMERGENCY_REVIEW',
      recommendation: 'Immediate physical examination and ECG',
      red_flags_detected: true,
      findings: [
        {
          rule_id: 'rule-cardio-1',
          category: 'Cardiovascular',
          severity: 'HIGH',
          matched_terms: ['chest pain', 'radiation'],
          clinical_rationale: 'Acute ischemic chest discomfort radiating to left arm',
        },
      ],
      evaluated_at: '2026-09-07T08:00:00Z',
    };

    render(<RedFlagAlert triage={mockTriage} />);

    expect(screen.getByText(/Emergency Clinical Review Required/i)).toBeInTheDocument();
    expect(screen.getByText(/Acute ischemic chest discomfort radiating to left arm/i)).toBeInTheDocument();
  });

  it('does not render RedFlagAlert if urgency is normal and no red flags detected', () => {
    const normalTriage: TriageResult = {
      consultation_id: 'consult-123',
      urgency_level: 'NORMAL',
      recommendation: 'Routine OPD consultation',
      red_flags_detected: false,
      findings: [],
      evaluated_at: '2026-09-07T08:00:00Z',
    };

    const { container } = render(<RedFlagAlert triage={normalTriage} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders SummaryTab with clinical findings and triggers review actions', async () => {
    const mockSummary: SummaryResponse = {
      id: 'sum-123',
      consultation_id: 'consult-123',
      status: 'draft',
      summary_text: 'Patient presents with acute chest discomfort starting 2 hours prior.',
      ai_draft_text: 'Patient presents with acute chest discomfort starting 2 hours prior.',
      generated_by: 'gemini-1.5-pro',
      version: 1,
      structured_summary: {
        chief_complaint: 'Chest heaviness',
        history_of_present_illness: 'Patient reports 2 hours of crushing central chest pressure.',
        patient_reported_symptoms: [
          {
            item: 'Crushing chest pressure',
            source_type: 'PATIENT_REPORTED',
            evidence: 'I feel heavy pressure on my chest',
          },
        ],
        past_medical_history: [],
        past_surgical_history: [],
        current_medications: [
          {
            name: 'Aspirin',
            dosage: '75mg',
            frequency: 'OD',
            source_type: 'DOCUMENT_EXTRACTED',
          },
        ],
        allergies: [],
        family_and_social_history: [],
        relevant_investigations: [],
        triage_and_red_flags: [],
        timeline_highlights: [],
        unreported_or_unclear_areas: [],
        disclaimer: 'Physician verification mandatory.',
      },
      reviewed_by_id: null,
      reviewed_at: null,
      clinician_notes: null,
      rejection_reason: null,
      created_at: '2026-09-07T08:05:00Z',
      updated_at: '2026-09-07T08:05:00Z',
    };

    const onEdit = vi.fn().mockResolvedValue(undefined);
    const onConfirm = vi.fn().mockResolvedValue(undefined);
    const onReject = vi.fn().mockResolvedValue(undefined);
    const onRegenerate = vi.fn().mockResolvedValue(undefined);

    render(
      <SummaryTab
        summary={mockSummary}
        isLoading={false}
        onEdit={onEdit}
        onConfirm={onConfirm}
        onReject={onReject}
        onRegenerate={onRegenerate}
      />
    );

    expect(screen.getByText(/Patient presents with acute chest discomfort starting 2 hours prior./i)).toBeInTheDocument();
    expect(screen.getByText(/Crushing chest pressure/i)).toBeInTheDocument();
    expect(screen.getByText(/Aspirin/i)).toBeInTheDocument();

    // Verify confirm modal interaction
    const confirmBtn = screen.getByRole('button', { name: /Confirm & Sign-off/i });
    fireEvent.click(confirmBtn);

    const modal = screen.getByRole('dialog');
    expect(screen.getByText(/Confirm & Finalize Clinical Summary/i)).toBeInTheDocument();
    const submitConfirm = within(modal).getByRole('button', { name: /Confirm & Sign-Off/i });
    fireEvent.click(submitConfirm);

    await waitFor(() => {
      expect(onConfirm).toHaveBeenCalled();
    });
  });
});
