export interface TimelineEvent {
  id: string;
  patient_id: string;
  consultation_id?: string | null;
  event_date: string | null;
  date_precision: string;
  event_type: string;
  title: string;
  description?: string | null;
  source_type: string;
  source_id?: string | null;
  source_page?: number | null;
  evidence?: string | null;
  verification_status: 'UNVERIFIED' | 'SOURCE_CONFIRMED' | 'CLINICIAN_VERIFIED' | string;
  created_at: string;
  updated_at: string;
}

export interface PatientTimelineResponse {
  patient_id: string;
  total_events: number;
  events: TimelineEvent[];
  generated_at: string;
}
