export interface ProvenanceItem {
  item: string;
  source_type: 'PATIENT_REPORTED' | 'DOCUMENT_EXTRACTED' | 'CLINICAL_HISTORY' | 'TRIAGE_ALERT' | 'CLINICIAN_ENTERED' | string;
  source_id?: string | null;
  evidence?: string | null;
}

export interface SummaryMedication {
  name: string;
  dosage?: string | null;
  frequency?: string | null;
  source_type: string;
  evidence?: string | null;
}

export interface SummaryAllergy {
  allergen: string;
  reaction?: string | null;
  severity?: string | null;
  source_type: string;
}

export interface SummaryInvestigation {
  test_name: string;
  result_value: string;
  unit?: string | null;
  reference_range?: string | null;
  flag?: string | null;
  source_document?: string | null;
  evidence?: string | null;
}

export interface SummaryTriageAlert {
  alert_type: string;
  severity: string;
  message: string;
  status: string;
}

export interface SummaryTimelineEvent {
  event_date?: string | null;
  event_type: string;
  title: string;
  verification_status: string;
}

export interface StructuredSummary {
  chief_complaint?: string | null;
  history_of_present_illness?: string | null;
  patient_reported_symptoms: ProvenanceItem[];
  past_medical_history: ProvenanceItem[];
  past_surgical_history: ProvenanceItem[];
  current_medications: SummaryMedication[];
  allergies: SummaryAllergy[];
  family_and_social_history: ProvenanceItem[];
  relevant_investigations: SummaryInvestigation[];
  triage_and_red_flags: SummaryTriageAlert[];
  timeline_highlights: SummaryTimelineEvent[];
  unreported_or_unclear_areas: string[];
  clinician_notes?: string | null;
  disclaimer: string;
}

export interface SummaryResponse {
  id: string;
  consultation_id: string;
  summary_text: string;
  structured_summary?: StructuredSummary | null;
  ai_draft_text?: string | null;
  generated_by: string;
  version: number;
  status: 'draft' | 'confirmed' | 'rejected' | string;
  reviewed_by_id?: string | null;
  reviewed_at?: string | null;
  clinician_notes?: string | null;
  rejection_reason?: string | null;
  created_at: string;
  updated_at: string;
}
