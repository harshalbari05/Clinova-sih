export interface TriageFinding {
  rule_id: string;
  category: string;
  severity: 'CRITICAL' | 'HIGH' | 'MODERATE' | 'LOW' | string;
  matched_terms: string[];
  clinical_rationale: string;
}

export interface TriageResult {
  consultation_id: string;
  urgency_level: 'EMERGENCY_REVIEW' | 'URGENT' | 'NORMAL' | string;
  red_flags_detected: boolean;
  findings: TriageFinding[];
  evaluated_at: string;
  recommendation?: string | null;
}

export interface AlertResponse {
  id: string;
  consultation_id: string;
  alert_type: string;
  severity: string;
  message: string;
  status: string;
  created_at: string;
}

export interface AlertListResponse {
  items: AlertResponse[];
  total: number;
}
