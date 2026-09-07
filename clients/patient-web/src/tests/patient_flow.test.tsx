import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { PatientProvider } from '../context/PatientContext';
import LandingPage from '../pages/LandingPage';
import ConsentPage from '../pages/ConsentPage';
import LanguagePage from '../pages/LanguagePage';
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
});
