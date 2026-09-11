/**
 * Clinova Patient Mobile Type Definitions
 * Directly matching FastAPI Pydantic schemas.
 */

export type UserRole = 'patient' | 'hospital' | 'doctor' | 'hospital_admin' | 'hospital_staff';

export interface User {
  id: string;
  email: string | null;
  phone: string | null;
  role: UserRole;
  is_active: boolean;
}

export interface Patient {
  id: string;
  user_id: string;
  full_name: string;
  phone?: string | null;
  email?: string | null;
  date_of_birth?: string | null;
  dob?: string | null;
  gender?: string | null;
  blood_group?: string | null;
  abha_id?: string | null;
  address?: string | null;
  emergency_contact?: string | null;
  created_at?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in?: number;
  account_type: 'patient' | 'hospital';
  user: User;
  patient?: Patient;
}

export interface Hospital {
  id: string;
  name: string;
  city?: string | null;
  state?: string | null;
}

export type ConsultationStatus =
  | 'initiated'
  | 'in_progress'
  | 'completed'
  | 'reviewed'
  | 'cancelled';

export interface Consultation {
  id: string;
  patient_id: string;
  hospital_id: string;
  status: ConsultationStatus;
  priority?: string | null;
  chief_complaint?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
  updated_at?: string;
}

export interface ConsultationListResponse {
  items: Consultation[];
  total: number;
  limit: number;
  offset: number;
}

export interface ConsentRecord {
  id: string;
  patient_id: string;
  consultation_id?: string | null;
  consent_type: string;
  granted: boolean;
  version: string;
  timestamp: string;
  revoked_at?: string | null;
}

export interface AISession {
  id: string;
  consultation_id: string;
  session_token: string;
  language: string;
  status: string;
  current_step?: string | null;
  started_at: string;
  completed_at?: string | null;
}

export interface AIMessage {
  id: string;
  session_id: string;
  role: 'patient' | 'assistant' | 'ai' | 'system';
  content: string;
  step?: string | null;
  current_step_label?: string | null;
  options?: string[];
  is_complete?: boolean;
  created_at?: string;
}

export interface AIInterviewMessageResponse {
  id: string;
  session_id: string;
  role: 'patient' | 'assistant' | 'ai' | 'system';
  content: string;
  step?: string | null;
  current_step_label?: string | null;
  options?: string[];
  is_complete?: boolean;
  created_at?: string;
}

export type TriagePriority =
  | 'red'
  | 'orange'
  | 'yellow'
  | 'green'
  | 'EMERGENCY'
  | 'URGENT'
  | 'NORMAL'
  | string;

export interface TriageResult {
  id: string;
  consultation_id: string;
  priority: TriagePriority;
  category?: string;
  red_flags_detected?: string[];
  trigger_symptoms?: string[];
  emergency_instructions?: string;
  requires_immediate_escalation?: boolean;
  is_red_flag?: boolean;
  triage_notes?: string;
  vital_signs_reviewed?: boolean;
  evaluated_at?: string;
  created_at?: string;
}

export interface ClinicalAlert {
  id: string;
  consultation_id: string;
  severity: string;
  title: string;
  description: string;
  created_at: string;
}

export type DocumentType =
  | 'prescription'
  | 'lab_report'
  | 'radiology_scan'
  | 'discharge_summary'
  | 'other'
  | string;

export type UploadStatus =
  | 'pending'
  | 'uploading'
  | 'uploaded'
  | 'processing'
  | 'processed'
  | 'failed'
  | string;

export interface MedicalDocument {
  id: string;
  patient_id: string;
  consultation_id?: string | null;
  file_name?: string;
  filename?: string;
  original_filename?: string;
  file_type?: string | null;
  file_size_bytes?: number | null;
  document_type: string;
  document_date?: string | null;
  mime_type?: string | null;
  upload_status?: UploadStatus;
  ocr_status?: string;
  processing_status?: string;
  created_at: string;
  uploaded_at?: string;
}

export interface StructuredExtraction {
  id?: string;
  document_id?: string;
  document_type?: string | null;
  confidence_score?: number | null;
  hospital_or_clinic_name?: string | null;
  doctor_name?: string | null;
  patient_name_as_written?: string | null;
  diagnosis?: string[] | null;
  diagnoses_or_conditions_as_documented?: string[];
  symptoms_as_documented?: string[];
  medications?: Array<{
    name: string;
    dosage?: string;
    frequency?: string;
    duration?: string;
    instructions?: string;
  }> | null;
  laboratory_results?: Array<{
    test_name: string;
    result_value?: string;
    unit?: string;
    reference_range?: string;
    flag?: string;
  }> | null;
  investigations?: string[];
  allergies?: string[];
  vitals?: Record<string, string | number> | null;
  procedures?: string[] | null;
  clinical_impressions?: string[] | null;
  follow_up_instructions_as_documented?: string | null;
  warnings?: string[];
  raw_summary?: string;
  cleaned_text?: string;
  extracted_at?: string;
}

export interface TimelineEvent {
  id: string;
  patient_id: string;
  event_type: string;
  event_date: string;
  date_precision: 'EXACT' | 'MONTH' | 'YEAR' | 'APPROXIMATE' | 'UNKNOWN' | string;
  title: string;
  description?: string | null;
  source_type: string;
  source_id?: string | null;
  source_page?: number | null;
  evidence_snippet?: string | null;
  verification_status: 'UNVERIFIED' | 'SOURCE_CONFIRMED' | 'CLINICIAN_VERIFIED' | string;
  is_verified?: boolean;
}

export interface PatientTimelineResponse {
  patient_id: string;
  total_events: number;
  events: TimelineEvent[];
  generated_at?: string;
}

export interface ClinicalSummary {
  id: string;
  consultation_id: string;
  summary_type?: string;
  summary_text?: string;
  narrative?: string | null;
  structured_summary?: Record<string, any> | null;
  structured_data?: Record<string, any> | null;
  verification_status?: 'draft' | 'reviewed' | 'confirmed' | 'rejected' | string;
  status?: string;
  version: number;
  ai_draft_text?: string | null;
  clinician_notes?: string | null;
  chief_complaint?: string | null;
  history_of_present_illness?: string | null;
  structured_findings?: Record<string, any>;
  created_at: string;
  updated_at?: string;
}

export interface ActiveVisit {
  has_active_visit: boolean;
  consultation_id?: string | null;
  hospital_id?: string | null;
  hospital_name?: string | null;
  department?: string | null;
  token_number?: number | null;
  now_serving?: number | null;
  people_ahead?: number | null;
  status?: string | null;
  checkin_time?: string | null;
}

