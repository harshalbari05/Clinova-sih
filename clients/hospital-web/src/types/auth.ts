export interface UserSummary {
  id: string;
  email: string | null;
  phone: string | null;
  full_name?: string | null;
  role: string;
  is_active: boolean;
  created_at: string | null;
}

export interface HospitalSummary {
  id: string;
  name: string;
  registration_number: string | null;
  phone: string | null;
  email: string | null;
  address: string | null;
  city: string | null;
  state: string | null;
  pincode: string | null;
  created_at: string | null;
}

export interface PatientProfile {
  id: string;
  user_id: string;
  full_name: string;
  date_of_birth: string | null;
  gender: string | null;
  phone: string | null;
  abha_id: string | null;
  address: string | null;
  emergency_contact: string | null;
  created_at: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserSummary;
  account_type: 'patient' | 'hospital';
  patient?: PatientProfile | null;
  hospital?: HospitalSummary | null;
  hospital_role?: string | null;
}

export interface CurrentUserResponse {
  user: UserSummary;
  account_type: 'patient' | 'hospital';
  patient?: PatientProfile | null;
  hospital?: HospitalSummary | null;
  hospital_role?: string | null;
}
