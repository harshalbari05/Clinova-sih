import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { PatientProvider } from '../context/PatientContext';
import LandingPage from '../pages/LandingPage';
import ConsentPage from '../pages/ConsentPage';
import LanguagePage from '../pages/LanguagePage';
import IdentifyPage from '../pages/IdentifyPage';
import InterviewPage from '../pages/InterviewPage';
import PriorityBadge from '../components/PriorityBadge';
import EmergencyOverlay from '../components/EmergencyOverlay';
import * as api from '../api';

// Mock API modules
vi.mock('../api', () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
    getMe: vi.fn(),
    getPatientProfile: vi.fn(),
  },
  hospitalApi: {
    listHospitals: vi.fn(),
  },
  consultationApi: {
    createConsultation: vi.fn(),
    recordConsent: vi.fn(),
    listConsultations: vi.fn(),
  },
  aiApi: {
    createSession: vi.fn(),
    sendMessage: vi.fn(),
    getSession: vi.fn(),
    completeSession: vi.fn(),
    listMessages: vi.fn(),
  },
  triageApi: {
    getTriageResult: vi.fn(),
  },
  documentApi: {
    uploadDocument: vi.fn(),
    processDocument: vi.fn(),
    getDocument: vi.fn(),
    getExtraction: vi.fn(),
    listDocuments: vi.fn(),
  },
  timelineApi: {
    getMyTimeline: vi.fn(),
    rebuildTimeline: vi.fn(),
  },
  summaryApi: {
    getSummary: vi.fn(),
    generateSummary: vi.fn(),
  },
}));

describe('Patient Portal Component Tests', () => {
  const mockPatient = {
    id: 'pat-1',
    user_id: 'usr-1',
    full_name: 'Rahul Sharma',
    date_of_birth: '1990-05-14',
    dob: '1990-05-14',
    gender: 'Male',
    blood_group: 'O+',
    abha_id: '91-4521-8890-1234',
    phone: '9876543210',
    created_at: new Date().toISOString(),
  };

  const mockConsultation = {
    id: 'con-101',
    patient_id: 'pat-1',
    hospital_id: 'hosp-1',
    chief_complaint: 'Cough and shortness of breath',
    priority: 'NORMAL',
    status: 'in_progress' as const,
    created_at: new Date().toISOString(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('renders LandingPage with Clinova branding and clinical clarity styling', () => {
    render(
      <MemoryRouter>
        <PatientProvider>
          <LandingPage />
        </PatientProvider>
      </MemoryRouter>
    );

    expect(screen.getByText(/Your Medical History,/i)).toBeInTheDocument();
    expect(screen.getByText(/Ready Before/i)).toBeInTheDocument();
    expect(screen.getByText(/Start Patient Intake/i)).toBeInTheDocument();
    expect(screen.getByText(/Existing Patient Sign-In/i)).toBeInTheDocument();
    expect(screen.getByText(/How Clinova Works/i)).toBeInTheDocument();
    expect(screen.getByText(/Physician-Supervised/i)).toBeInTheDocument();
  });

  it('renders PriorityBadge correctly for each triage level', () => {
    const { rerender } = render(<PriorityBadge priority="red" />);
    expect(screen.getByText(/Emergency \(Red\)/i)).toBeInTheDocument();

    rerender(<PriorityBadge priority="orange" />);
    expect(screen.getByText(/Urgent \(Orange\)/i)).toBeInTheDocument();

    rerender(<PriorityBadge priority="green" />);
    expect(screen.getByText(/Routine \(Green\)/i)).toBeInTheDocument();
  });

  it('renders EmergencyOverlay when red-flag triage alert is triggered', () => {
    const mockTriage = {
      id: 'tri-123',
      consultation_id: 'con-456',
      priority: 'red',
      is_red_flag: true,
      triage_notes: 'Patient reports acute crushing chest pain radiating to left arm.',
      vital_signs_reviewed: true,
      created_at: new Date().toISOString(),
    };

    const handleAck = vi.fn();

    render(
      <EmergencyOverlay 
        triageResult={mockTriage} 
        onAcknowledge={handleAck} 
      />
    );

    expect(screen.getByText(/POTENTIAL EMERGENCY DETECTED/i)).toBeInTheDocument();
    expect(screen.getByText(/Please notify OPD nursing staff immediately/i)).toBeInTheDocument();
    expect(screen.getByText(/Patient reports acute crushing chest pain/i)).toBeInTheDocument();

    const ackBtn = screen.getByText(/I Have Notified Medical Staff/i);
    fireEvent.click(ackBtn);
    expect(handleAck).toHaveBeenCalledTimes(1);
  });

  it('renders LanguagePage and marks AYUSH as Phase 2 / Disabled', () => {
    localStorage.setItem('clinova_patient_token', 'mock-token');
    localStorage.setItem('clinova_patient_data', JSON.stringify(mockPatient));
    localStorage.setItem('clinova_active_consultation', JSON.stringify(mockConsultation));

    render(
      <MemoryRouter>
        <PatientProvider>
          <LanguagePage />
        </PatientProvider>
      </MemoryRouter>
    );

    expect(screen.getByText(/Select Your Preferred Language/i)).toBeInTheDocument();
    expect(screen.getAllByText(/English/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Hindi/i)).toBeInTheDocument();
    expect(screen.getByText(/Marathi/i)).toBeInTheDocument();
    expect(screen.getByText(/AYUSH Intake/i)).toBeInTheDocument();
    expect(screen.getByText(/PHASE 2/i)).toBeInTheDocument();
  });

  it('records patient consent via POST /consultations/{id}/consent', async () => {
    localStorage.setItem('clinova_patient_token', 'mock-token');
    localStorage.setItem('clinova_patient_data', JSON.stringify(mockPatient));
    localStorage.setItem('clinova_active_consultation', JSON.stringify(mockConsultation));

    (api.consultationApi.recordConsent as any).mockResolvedValue({
      id: 'consent-1',
      consultation_id: 'con-101',
      patient_id: 'pat-1',
      consent_type: 'clinical_intake',
      granted: true,
      version: '1.0',
      timestamp: new Date().toISOString(),
    });

    render(
      <MemoryRouter>
        <PatientProvider>
          <ConsentPage />
        </PatientProvider>
      </MemoryRouter>
    );

    expect(screen.getByText(/Informed Patient Consent/i)).toBeInTheDocument();
    expect(screen.getByText(/AI-Assisted Adaptive Interview/i)).toBeInTheDocument();
    expect(screen.getByText(/Physician Authority & Review/i)).toBeInTheDocument();

    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).not.toBeChecked();

    const continueBtn = screen.getByRole('button', { name: /I Agree • Continue/i });
    expect(continueBtn).toBeDisabled();

    // Check the box
    fireEvent.click(checkbox);
    expect(checkbox).toBeChecked();
    expect(continueBtn).not.toBeDisabled();

    // Click submit
    fireEvent.click(continueBtn);

    await waitFor(() => {
      expect(api.consultationApi.recordConsent).toHaveBeenCalledWith('con-101', {
        consent_given: true,
        consent_type: 'clinical_intake',
      });
    });
  });

  it('renders SummaryPage with clinical summary and submits with live consultation reference ID', async () => {
    localStorage.setItem('clinova_patient_token', 'mock-token');
    localStorage.setItem('clinova_patient_data', JSON.stringify(mockPatient));
    localStorage.setItem('clinova_active_consultation', JSON.stringify(mockConsultation));

    const mockSummaryData = {
      id: 'sum-101',
      consultation_id: 'con-101',
      patient_id: 'pat-1',
      status: 'draft',
      chief_complaint: 'Cough and shortness of breath',
      provisional_diagnosis: 'Acute Bronchitis',
      summary_text: 'Patient reports 4 days of dry cough and low grade fever.',
      differential_diagnoses: [],
      red_flags: [],
      recommendations: [],
      structured_summary: {
        chief_complaint: 'Cough and shortness of breath',
        patient_reported_symptoms: [],
        past_medical_history: [],
        current_medications: [],
        allergies: [],
      },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    (api.summaryApi.getSummary as any).mockResolvedValue(mockSummaryData);
    (api.documentApi.listDocuments as any).mockResolvedValue({ items: [], total: 0 });

    const SummaryPageMod = (await import('../pages/SummaryPage')).default;

    render(
      <MemoryRouter>
        <PatientProvider>
          <SummaryPageMod />
        </PatientProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Review Your Information/i)).toBeInTheDocument();
      expect(screen.getByText(/Patient reports 4 days of dry cough and low grade fever./i)).toBeInTheDocument();
    });

    // Acknowledge review checkbox
    const confirmCheckbox = screen.getByRole('checkbox');
    fireEvent.click(confirmCheckbox);

    // Wait for state update so button is enabled
    const submitBtn = screen.getByRole('button', { name: /Submit to Doctor Queue/i });
    await waitFor(() => {
      expect(submitBtn).not.toBeDisabled();
    });
    fireEvent.click(submitBtn);

    // Verify modal overlay opens with live consultation reference ID
    await waitFor(() => {
      expect(screen.getByText(/Submitted Successfully!/i)).toBeInTheDocument();
      expect(screen.getByText(/Consultation Case Reference/i)).toBeInTheDocument();
      const refElements = screen.getAllByText(/CON-101/i);
      expect(refElements.length).toBeGreaterThanOrEqual(2);
      expect(screen.queryByText('#24')).not.toBeInTheDocument();
    });
  });

  it('loads hospitals, opens selector, displays hospitals, selects a hospital, and submits consultation with selected hospital ID', async () => {
    const mockHospitals = [
      { id: 'hosp-1', name: 'AIIMS Delhi', city: 'New Delhi', state: 'Delhi' },
      { id: 'hosp-2', name: 'Clinova General Hospital', city: 'Pune', state: 'Maharashtra' },
      { id: 'hosp-3', name: 'Demo Hospital', city: 'Mumbai', state: 'Maharashtra' },
    ];

    (api.hospitalApi.listHospitals as any).mockResolvedValue(mockHospitals);
    (api.authApi.register as any).mockResolvedValue({ id: 'usr-new' });
    (api.authApi.login as any).mockResolvedValue({
      access_token: 'new-token',
      token_type: 'bearer',
      account_type: 'patient',
      user: { id: 'usr-new', email: 'ramesh@example.com', role: 'patient', is_active: true },
      patient: mockPatient,
    });
    (api.consultationApi.createConsultation as any).mockResolvedValue({
      id: 'con-202',
      patient_id: 'pat-1',
      hospital_id: 'hosp-2',
      chief_complaint: 'High fever',
      status: 'initiated',
      created_at: new Date().toISOString(),
    });

    render(
      <MemoryRouter>
        <PatientProvider>
          <IdentifyPage />
        </PatientProvider>
      </MemoryRouter>
    );

    // 1. Verify hospitals are loaded and initial selector renders
    await waitFor(() => {
      expect(screen.getAllByText('AIIMS Delhi').length).toBeGreaterThanOrEqual(1);
    });

    // 2. Click hospital selector to open dropdown menu
    const selectorBtn = screen.getByTestId('hospital-selector');
    expect(selectorBtn).toHaveAttribute('aria-expanded', 'false');
    fireEvent.click(selectorBtn);

    // 3. Verify dropdown menu opens and displays all hospitals
    await waitFor(() => {
      expect(selectorBtn).toHaveAttribute('aria-expanded', 'true');
      expect(screen.getByTestId('hospital-dropdown-menu')).toBeInTheDocument();
      expect(screen.getAllByText('Clinova General Hospital').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Demo Hospital').length).toBeGreaterThanOrEqual(1);
    });

    // 4. Select a hospital (Clinova General Hospital)
    const optionHosp2 = screen.getByTestId('hospital-option-hosp-2');
    fireEvent.click(optionHosp2);

    // 5. Verify dropdown closes and selected hospital is reflected in UI
    await waitFor(() => {
      expect(selectorBtn).toHaveAttribute('aria-expanded', 'false');
      expect(screen.queryByTestId('hospital-dropdown-menu')).not.toBeInTheDocument();
      expect(screen.getAllByText('Clinova General Hospital').length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText(/Pune, Maharashtra/i)).toBeInTheDocument();
    });

    // 6. Fill required fields and submit form
    const nameInput = screen.getByPlaceholderText(/e\.g\. Ramesh Kumar/i);
    const emailInput = screen.getByPlaceholderText(/patient@example\.com/i);
    const complaintInput = screen.getByPlaceholderText(/e\.g\. High fever/i);

    fireEvent.change(nameInput, { target: { value: 'Ramesh Kumar' } });
    fireEvent.change(emailInput, { target: { value: 'ramesh@example.com' } });
    fireEvent.change(complaintInput, { target: { value: 'High fever' } });

    const continueBtn = screen.getByRole('button', { name: /Continue to Informed Consent/i });
    fireEvent.click(continueBtn);

    // 7. Verify consultation is created using selected hospital ID
    await waitFor(() => {
      expect(api.consultationApi.createConsultation).toHaveBeenCalledWith(
        expect.objectContaining({
          hospital_id: 'hosp-2',
          chief_complaint: 'High fever',
        })
      );
    });
  });

  it('completes AI interview upon final turn, displays final message, calls complete session API, and navigates to /upload', async () => {
    const mockSession = {
      id: 'sess-intake-99',
      consultation_id: 'con-101',
      language: 'English',
      status: 'in_progress',
      started_at: new Date().toISOString(),
      completed_at: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    localStorage.setItem('clinova_patient_token', 'mock-token');
    localStorage.setItem('clinova_patient_data', JSON.stringify(mockPatient));
    localStorage.setItem('clinova_active_consultation', JSON.stringify(mockConsultation));
    localStorage.setItem('clinova_active_session', JSON.stringify(mockSession));

    const initialMessages = [
      {
        id: 'msg-ai-1',
        session_id: 'sess-intake-99',
        role: 'ai' as const,
        content: 'Are you experiencing any other symptoms, such as fever, cough, chest discomfort, or headache?',
        step: 'review_of_systems',
        current_step_label: 'Review of Systems',
        options: ['No other symptoms', 'Mild headache'],
        is_complete: false,
        created_at: new Date().toISOString(),
      },
    ];

    (api.aiApi.listMessages as any).mockResolvedValue({
      items: initialMessages,
      total: 1,
    });
    (api.aiApi.getSession as any).mockResolvedValue(mockSession);

    const finalAIMessageResponse = {
      id: 'msg-final-turn',
      session_id: 'sess-intake-99',
      role: 'ai' as const,
      content: 'Thank you for providing your details. Your clinical history intake is complete. The doctor will review your history during your consultation.',
      step: 'review_of_systems',
      current_step_label: 'Clinical Intake Complete',
      options: [],
      is_complete: true,
      patient_message: {
        id: 'msg-pat-final',
        session_id: 'sess-intake-99',
        role: 'patient',
        content: 'No other symptoms',
        created_at: new Date().toISOString(),
      },
      interview: {
        next_question: 'Thank you for providing your details. Your clinical history intake is complete. The doctor will review your history during your consultation.',
        current_section: 'review_of_systems',
        interview_complete: true,
        missing_information: [],
        is_fallback: true,
      },
    };

    (api.aiApi.sendMessage as any).mockResolvedValue(finalAIMessageResponse);
    (api.aiApi.completeSession as any).mockResolvedValue({
      ...mockSession,
      status: 'completed',
      completed_at: new Date().toISOString(),
    });

    render(
      <MemoryRouter initialEntries={['/interview']}>
        <PatientProvider>
          <Routes>
            <Route path="/interview" element={<InterviewPage />} />
            <Route path="/upload" element={<div data-testid="upload-page">Document Upload Screen</div>} />
          </Routes>
        </PatientProvider>
      </MemoryRouter>
    );

    // 1. Initial message rendered
    await waitFor(() => {
      expect(screen.getByText(/Are you experiencing any other symptoms/i)).toBeInTheDocument();
    });

    // 2. Patient submits final response
    const textarea = screen.getByPlaceholderText(/Type your response in English/i);
    fireEvent.change(textarea, { target: { value: 'No other symptoms' } });
    const sendBtn = screen.getByTitle('Send Message');
    fireEvent.click(sendBtn);

    // 3. Final AI completion response is rendered
    await waitFor(() => {
      expect(api.aiApi.sendMessage).toHaveBeenCalledWith('sess-intake-99', 'No other symptoms');
    });

    await waitFor(() => {
      expect(screen.getByText(/Your clinical history intake is complete/i)).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: /Clinical Intake Complete/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Continue to Medical Documents/i })).toBeInTheDocument();
    });

    // 4. Click completion action to advance to Step 5
    const continueBtn = screen.getByRole('button', { name: /Continue to Medical Documents/i });
    fireEvent.click(continueBtn);

    // 5. Verify completeSession API was called
    await waitFor(() => {
      expect(api.aiApi.completeSession).toHaveBeenCalledWith('sess-intake-99');
    });

    // 6. Verify navigation to /upload succeeded
    await waitFor(() => {
      expect(screen.getByTestId('upload-page')).toBeInTheDocument();
    });
  });
});

