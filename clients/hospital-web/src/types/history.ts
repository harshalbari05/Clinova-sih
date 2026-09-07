export interface ClinicalHistoryResponse {
  id: string;
  consultation_id: string;
  chief_complaint?: string | null;
  history_of_present_illness?: string | null;
  past_medical_history?: string | null;
  past_surgical_history?: string | null;
  drug_history?: string | null;
  allergy_history?: string | null;
  family_history?: string | null;
  personal_history?: string | null;
  review_of_systems?: string | null;
  created_at: string;
  updated_at: string;
}
