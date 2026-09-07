export interface MedicalDocument {
  id: string;
  patient_id: string;
  consultation_id?: string | null;
  document_type: string;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  document_date?: string | null;
  processing_state: 'uploaded' | 'processing' | 'completed' | 'failed' | string;
  error_message?: string | null;
  ocr_extracted: boolean;
  ai_extracted: boolean;
  created_at: string;
  updated_at: string;
}

export interface MedicalDocumentListResponse {
  items: MedicalDocument[];
  total: number;
  limit: number;
  offset: number;
}

export interface ExtractedLabResult {
  test_name: string;
  result_value: string;
  unit?: string | null;
  reference_range?: string | null;
  flag?: string | null;
  source_page?: number | null;
  evidence?: string | null;
}

export interface ExtractedMedication {
  name: string;
  dosage?: string | null;
  frequency?: string | null;
  duration?: string | null;
  evidence?: string | null;
}

export interface ExtractedDiagnosis {
  diagnosis: string;
  status?: string | null;
  evidence?: string | null;
}

export interface StructuredClinicalData {
  document_type?: string | null;
  report_date?: string | null;
  doctor_name?: string | null;
  hospital_name?: string | null;
  diagnoses: ExtractedDiagnosis[];
  medications: ExtractedMedication[];
  lab_results: ExtractedLabResult[];
  vital_signs: Record<string, string | number>;
  clinical_notes?: string | null;
  disclaimer: string;
}

export interface ExtractedDataResponse {
  document_id: string;
  ocr_text?: string | null;
  structured_data?: StructuredClinicalData | null;
  extraction_status: string;
  extracted_at?: string | null;
}
