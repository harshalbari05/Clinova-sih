/**
 * Types for Hospital Reception and Patient Registration.
 *
 * Strictly non-clinical: contains only demographic and visit routing metadata.
 */

export interface SafePatientLookup {
  patient_id: string;
  full_name: string;
  date_of_birth?: string | null;
  age?: number | null;
  gender?: string | null;
  phone?: string | null;
  abha_id?: string | null;
  blood_group?: string | null;
  has_active_intake: boolean;
  active_consultation_id?: string | null;
}

export interface ConfirmRegistrationPayload {
  patient_id: string;
  department: string;
  consultation_id?: string | null;
}

export interface ManualRegistrationPayload {
  full_name: string;
  phone: string;
  date_of_birth?: string | null;
  age?: number | null;
  gender?: string | null;
  abha_id?: string | null;
  department: string;
  chief_complaint?: string;
}

export interface RegistrationResponse {
  consultation_id: string;
  patient_id: string;
  patient_name: string;
  hospital_id: string;
  hospital_name: string;
  department: string;
  token_number: number;
  status: string;
  message: string;
  created_at: string;
}

export interface DepartmentsResponse {
  departments: string[];
}

export interface QueueEntry {
  token_number: number;
  token?: number;
  patient_display_name: string;
  department: string;
  status: "waiting" | "in_progress" | "completed";
  position: number;
  consultation_id: string;
  checkin_time: string;
  chief_complaint?: string | null;
}

export interface DepartmentQueueResponse {
  hospital_id: string;
  hospital_name: string;
  department: string;
  now_serving: number | null;
  waiting_count: number;
  entries: QueueEntry[];
}

export interface AdvanceQueueResponse {
  department: string;
  previous_token?: number | null;
  now_serving?: number | null;
  message: string;
}
