import { apiClient } from './client';
import { TokenResponse, CurrentUserResponse } from '../types/auth';

export interface HospitalRegisterPayload {
  hospital_name: string;
  admin_email: string;
  admin_password: string;
  admin_name: string;
  registration_number?: string;
  hospital_phone?: string;
  hospital_email?: string;
  address?: string;
  city?: string;
  state?: string;
  pincode?: string;
}

export async function registerHospital(payload: HospitalRegisterPayload): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>('/auth/hospital/register', payload);
  return response.data;
}

export async function loginHospital(identifier: string, password: string): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>('/auth/hospital/login', {
    identifier,
    password,
  });
  return response.data;
}

export async function getMe(): Promise<CurrentUserResponse> {
  const response = await apiClient.get<CurrentUserResponse>('/auth/me');
  return response.data;
}

export async function logout(): Promise<{ message: string }> {
  try {
    const response = await apiClient.post<{ message: string }>('/auth/logout');
    return response.data;
  } finally {
    localStorage.removeItem('clinova_hospital_token');
    localStorage.removeItem('clinova_hospital_user');
    localStorage.removeItem('clinova_hospital_info');
    localStorage.removeItem('clinova_hospital_role');
  }
}
