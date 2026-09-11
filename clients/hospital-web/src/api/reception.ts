import { apiClient } from './client';
import {
  SafePatientLookup,
  ConfirmRegistrationPayload,
  ManualRegistrationPayload,
  RegistrationResponse,
  DepartmentsResponse,
  DepartmentQueueResponse,
  AdvanceQueueResponse,
} from '../types/reception';

export async function lookupPatientByQR(qrCode: string): Promise<SafePatientLookup> {
  const response = await apiClient.post<SafePatientLookup>('/reception/lookup-qr', {
    qr_code: qrCode,
  });
  return response.data;
}

export async function confirmRegistration(
  payload: ConfirmRegistrationPayload
): Promise<RegistrationResponse> {
  const response = await apiClient.post<RegistrationResponse>(
    '/reception/register-patient',
    payload
  );
  return response.data;
}

export async function registerManual(
  payload: ManualRegistrationPayload
): Promise<RegistrationResponse> {
  const response = await apiClient.post<RegistrationResponse>(
    '/reception/register-manual',
    payload
  );
  return response.data;
}

export async function getDepartments(): Promise<string[]> {
  const response = await apiClient.get<DepartmentsResponse>('/reception/departments');
  return response.data.departments;
}

export async function getDepartmentQueue(department: string): Promise<DepartmentQueueResponse> {
  const response = await apiClient.get<DepartmentQueueResponse>('/reception/queue', {
    params: { department },
  });
  return response.data;
}

export async function advanceDepartmentQueue(department: string): Promise<AdvanceQueueResponse> {
  const response = await apiClient.post<AdvanceQueueResponse>('/reception/queue/advance', {
    department,
  });
  return response.data;
}
