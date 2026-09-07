import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { LoginPage } from '../pages/LoginPage';
import { TokenResponse } from '../types/auth';
import * as authApi from '../api/auth';

vi.mock('../api/auth');

describe('Hospital Staff Authentication', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('renders login form with clinical title and staff identifier inputs', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <LoginPage />
        </BrowserRouter>
      </AuthProvider>
    );

    expect(screen.getByText(/Clinova Clinical Portal/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/doctor@hospital.org/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/••••••••••••/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Access Clinical Portal/i })).toBeInTheDocument();
  });

  it('switches between Staff Login and Register Facility tabs', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <LoginPage />
        </BrowserRouter>
      </AuthProvider>
    );

    const registerTab = screen.getByRole('button', { name: /Register Facility/i });
    fireEvent.click(registerTab);

    expect(screen.getByPlaceholderText(/AIIMS New Delhi/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Dr. Amit Sharma/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Create Hospital Facility/i })).toBeInTheDocument();
  });

  it('fills quick demo doctor credentials upon clicking Quick Demo Fill', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <LoginPage />
        </BrowserRouter>
      </AuthProvider>
    );

    const quickDemoBtn = screen.getByText(/Quick Demo Fill/i);
    fireEvent.click(quickDemoBtn);

    const identifierInput = screen.getByPlaceholderText(/doctor@hospital.org/i) as HTMLInputElement;
    expect(identifierInput.value).toBe('doctor@aiims.edu');
  });

  it('calls loginHospital API when form is submitted', async () => {
    const mockResponse: TokenResponse = {
      access_token: 'mock-jwt-token',
      token_type: 'bearer',
      expires_in: 3600,
      account_type: 'hospital',
      user: {
        id: 'u-123',
        email: 'doctor@aiims.edu',
        phone: null,
        full_name: 'Dr. Amit Sharma',
        role: 'doctor',
        is_active: true,
        created_at: '2026-09-07T08:00:00Z',
      },
      hospital: {
        id: 'h-123',
        name: 'AIIMS New Delhi',
        registration_number: 'AIIMS-1',
        phone: '011-26588500',
        email: 'info@aiims.edu',
        address: 'Ansari Nagar',
        city: 'New Delhi',
        state: 'Delhi',
        pincode: '110029',
        created_at: '2026-09-07T08:00:00Z',
      },
      hospital_role: 'doctor',
    };

    vi.mocked(authApi.loginHospital).mockResolvedValueOnce(mockResponse);

    render(
      <AuthProvider>
        <BrowserRouter>
          <LoginPage />
        </BrowserRouter>
      </AuthProvider>
    );

    fireEvent.change(screen.getByPlaceholderText(/doctor@hospital.org/i), {
      target: { value: 'doctor@aiims.edu' },
    });
    fireEvent.change(screen.getByPlaceholderText(/••••••••••••/i), {
      target: { value: 'HospitalPass123!' },
    });

    fireEvent.click(screen.getByRole('button', { name: /Access Clinical Portal/i }));

    await waitFor(() => {
      expect(authApi.loginHospital).toHaveBeenCalledWith('doctor@aiims.edu', 'HospitalPass123!');
      expect(localStorage.getItem('clinova_hospital_token')).toBe('mock-jwt-token');
    });
  });
});
