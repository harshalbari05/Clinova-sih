export interface Consultation {
  id: string;
  patient_id: string;
  hospital_id: string;
  status: 'initiated' | 'in_progress' | 'completed' | 'reviewed' | 'cancelled' | string;
  chief_complaint: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConsultationListResponse {
  items: Consultation[];
  total: number;
  limit: number;
  offset: number;
}
