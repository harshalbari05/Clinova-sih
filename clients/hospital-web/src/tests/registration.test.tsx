import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter, MemoryRouter, Routes, Route } from 'react-router-dom';
import { RegistrationPage } from '../pages/RegistrationPage';
import { ConsultationPage } from '../pages/ConsultationPage';
import * as receptionApi from '../api/reception';
import * as authContext from '../context/AuthContext';
import { SafePatientLookup, RegistrationResponse } from '../types/reception';

// Mock the reception API
vi.mock('../api/reception', () => ({
  lookupPatientByQR: vi.fn(),
  confirmRegistration: vi.fn(),
  registerManual: vi.fn(),
  getDepartments: vi.fn(),
}));

// Mock AuthContext
vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

describe('Hospital Reception Registration Workflow', () => {
  const mockDepartments = ['General Medicine', 'Pediatrics', 'Orthopedics', 'ENT'];

  const mockSafePatient: SafePatientLookup = {
    patient_id: 'dcc17922-076e-4187-a23f-015ed6c7b9ac',
    full_name: 'Rohan Patil',
    age: 34,
    gender: 'Male',
    phone: '9876543210',
    abha_id: '12-3456-7890-1234',
    has_active_intake: true,
    active_consultation_id: 'con-123-uuid',
  };

  const mockRegistrationResponse: RegistrationResponse = {
    consultation_id: 'con-123-uuid',
    patient_id: 'dcc17922-076e-4187-a23f-015ed6c7b9ac',
    patient_name: 'Rohan Patil',
    hospital_id: 'hosp-1-uuid',
    hospital_name: 'Demo General Hospital',
    department: 'General Medicine',
    token_number: 27,
    status: 'initiated',
    message: 'Patient registered successfully for General Medicine.',
    created_at: new Date().toISOString(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(receptionApi.getDepartments).mockResolvedValue(mockDepartments);
    vi.mocked(authContext.useAuth).mockReturnValue({
      user: {
        id: 'rec-1',
        email: 'reception@demohospital.org',
        phone: null,
        role: 'receptionist',
        is_active: true,
        created_at: null,
      },
      hospital: {
        id: 'hosp-1',
        name: 'Demo General Hospital',
        registration_number: 'HOSP-12345',
        phone: null,
        email: null,
        address: null,
        city: 'Mumbai',
        state: 'Maharashtra',
        pincode: null,
        created_at: null,
      },
      hospitalRole: 'receptionist',
      token: 'mock-token',
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
    });
  });

  it('renders registration page with header, QR mode, and manual mode toggle', async () => {
    render(
      <BrowserRouter>
        <RegistrationPage />
      </BrowserRouter>
    );

    expect(screen.getByText('Patient Visit Registration')).toBeInTheDocument();
    expect(screen.getByText(/Hospital Reception Desk/i)).toBeInTheDocument();
    expect(screen.getByText('Scan QR')).toBeInTheDocument();
    expect(screen.getByText('Manual Entry')).toBeInTheDocument();
    expect(screen.getByText(/Scan Patient Clinova QR/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/CLINOVA:PATIENT:.../i)).toBeInTheDocument();
    expect(screen.getByText(/SIH Quick Demo: Instant QR Simulator/i)).toBeInTheDocument();
  });

  it('allows looking up patient via QR and displays safe demographic profile without clinical history', async () => {
    vi.mocked(receptionApi.lookupPatientByQR).mockResolvedValue(mockSafePatient);

    render(
      <BrowserRouter>
        <RegistrationPage />
      </BrowserRouter>
    );

    const input = screen.getByPlaceholderText(/CLINOVA:PATIENT:.../i);
    fireEvent.change(input, {
      target: { value: 'CLINOVA:PATIENT:dcc17922-076e-4187-a23f-015ed6c7b9ac' },
    });

    const lookupBtn = screen.getByRole('button', { name: /Lookup/i });
    fireEvent.click(lookupBtn);

    await waitFor(() => {
      expect(receptionApi.lookupPatientByQR).toHaveBeenCalledWith(
        'CLINOVA:PATIENT:dcc17922-076e-4187-a23f-015ed6c7b9ac'
      );
    });

    // Verify safe demographic fields are rendered
    await waitFor(() => {
      expect(screen.getByText('Rohan Patil')).toBeInTheDocument();
      expect(screen.getByText(/34 Y • Male/i)).toBeInTheDocument();
      expect(screen.getByText('9876543210')).toBeInTheDocument();
      expect(screen.getByText('12-3456-7890-1234')).toBeInTheDocument();
      expect(screen.getByText(/Data Protection Guarantee/i)).toBeInTheDocument();
      expect(screen.getByText(/Pre-Hospital AI Intake Completed/i)).toBeInTheDocument();
    });

    // Ensure no clinical history or summary headers are present
    expect(screen.queryByText(/AI Clinical Summary/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Medical History/i)).not.toBeInTheDocument();
  });

  it('requires department selection and completes patient registration', async () => {
    vi.mocked(receptionApi.lookupPatientByQR).mockResolvedValue(mockSafePatient);
    vi.mocked(receptionApi.confirmRegistration).mockResolvedValue(mockRegistrationResponse);

    render(
      <BrowserRouter>
        <RegistrationPage />
      </BrowserRouter>
    );

    // Quick demo click on Rohan Patil
    const rohanDemoBtn = screen.getByRole('button', { name: /Rohan Patil/i });
    fireEvent.click(rohanDemoBtn);

    await waitFor(() => {
      expect(screen.getByText('Assign OPD Department for this Visit')).toBeInTheDocument();
    });

    // Select Orthopedics
    const orthoBtn = screen.getByRole('button', { name: /Orthopedics/i });
    fireEvent.click(orthoBtn);

    // Confirm registration
    const registerBtn = screen.getByRole('button', { name: /Confirm & Register/i });
    fireEvent.click(registerBtn);

    await waitFor(() => {
      expect(receptionApi.confirmRegistration).toHaveBeenCalledWith({
        patient_id: 'dcc17922-076e-4187-a23f-015ed6c7b9ac',
        department: 'Orthopedics',
        consultation_id: 'con-123-uuid',
      });
      expect(screen.getByText('Registration Successful')).toBeInTheDocument();
      expect(screen.getByText(/Register Next Patient/i)).toBeInTheDocument();
    });
  });

  it('handles manual walk-in fallback without searching existing patient profiles', async () => {
    vi.mocked(receptionApi.registerManual).mockResolvedValue({
      ...mockRegistrationResponse,
      patient_name: 'Suresh Patil',
      department: 'Pediatrics',
    });

    render(
      <BrowserRouter>
        <RegistrationPage />
      </BrowserRouter>
    );

    // Switch to manual mode
    const manualTab = screen.getByRole('button', { name: /Manual Entry/i });
    fireEvent.click(manualTab);

    expect(screen.getByText('Walk-in Patient Registration')).toBeInTheDocument();
    expect(screen.getByText(/No profile search is performed/i)).toBeInTheDocument();

    // Fill form
    fireEvent.change(screen.getByPlaceholderText(/e\.g\. Ramesh Kumar/i), {
      target: { value: 'Suresh Patil' },
    });
    fireEvent.change(screen.getByPlaceholderText(/10-digit mobile number/i), {
      target: { value: '9820098200' },
    });
    fireEvent.change(screen.getByPlaceholderText(/e\.g\. 42/i), {
      target: { value: '28' },
    });

    // Select Pediatrics department
    const pediatricsBtn = screen.getByRole('button', { name: /Pediatrics/i });
    fireEvent.click(pediatricsBtn);

    // Submit manual registration
    const submitBtn = screen.getByRole('button', { name: /Register Walk-in Patient/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(receptionApi.registerManual).toHaveBeenCalledWith(
        expect.objectContaining({
          full_name: 'Suresh Patil',
          phone: '9820098200',
          age: 28,
          gender: 'Male',
          department: 'Pediatrics',
        })
      );
      expect(screen.getByText('Registration Successful')).toBeInTheDocument();
    });
  });

  it('blocks receptionist role from viewing clinical consultation workspace', async () => {
    // Receptionist trying to view /consultation/con-123
    render(
      <MemoryRouter initialEntries={['/consultation/con-123']}>
        <Routes>
          <Route path="/consultation/:id" element={<ConsultationPage />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('Clinical Privacy Protection')).toBeInTheDocument();
    expect(
      screen.getByText(/Reception staff do not have authorization to view AI clinical summaries/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/Return to Patient Registration/i)).toBeInTheDocument();
  });
});
