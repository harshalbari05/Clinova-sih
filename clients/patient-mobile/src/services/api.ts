/**
 * Central Clinova Backend API Client
 * Connects directly to the existing FastAPI backend endpoints with token injection and error handling.
 */
import axios, { AxiosError, AxiosInstance } from 'axios';
import { getApiBaseUrl } from '../config/env';
import { getSecureItem, STORAGE_KEYS } from './storage';
import {
  AuthResponse,
  Patient,
  Hospital,
  Consultation,
  ConsultationListResponse,
  ConsentRecord,
  AISession,
  AIMessage,
  AIInterviewMessageResponse,
  TriageResult,
  MedicalDocument,
  StructuredExtraction,
  TimelineListResponse,
  ClinicalSummary,
} from '../types';

// Pending request registry for duplicate submission protection
const pendingRequests = new Set<string>();

const createClient = (): AxiosInstance => {
  const instance = axios.create({
    baseURL: getApiBaseUrl(),
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
  });

  instance.interceptors.request.use(async (config) => {
    // Dynamic base URL update in case it was changed at runtime
    config.baseURL = getApiBaseUrl();

    // Attach JWT token if available
    const token = await getSecureItem(STORAGE_KEYS.ACCESS_TOKEN);
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  instance.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
      // Friendly, non-technical error mapping without exposing raw stack traces
      let friendlyMessage = 'Unable to connect to healthcare server. Please check your internet connection.';

      if (error.response) {
        const status = error.response.status;
        const detail = (error.response.data as any)?.detail;

        if (status === 401) {
          friendlyMessage = 'Your session has expired. Please sign in again.';
        } else if (status === 403) {
          friendlyMessage = 'Access not authorized for this record.';
        } else if (status === 404) {
          friendlyMessage = 'The requested medical record was not found.';
        } else if (status === 409) {
          friendlyMessage = typeof detail === 'string' ? detail : 'Conflict with existing record.';
        } else if (status === 413) {
          friendlyMessage = 'Document is too large. Please upload an image under 10MB.';
        } else if (status === 422) {
          friendlyMessage = typeof detail === 'string' ? detail : 'Please check the entered information.';
        } else if (status === 429) {
          friendlyMessage = 'Too many requests. Please wait a moment before trying again.';
        } else if (status >= 500) {
          friendlyMessage = 'The healthcare service is temporarily unavailable. Please try again shortly.';
        } else if (typeof detail === 'string') {
          friendlyMessage = detail;
        }
      }

      return Promise.reject(new Error(friendlyMessage));
    }
  );

  return instance;
};

const client = createClient();

export const api = {
  // ================= AUTH =================
  async registerPatient(data: {
    email: string;
    password?: string;
    full_name: string;
    phone?: string;
    abha_id?: string;
    dob?: string;
    gender?: string;
  }): Promise<AuthResponse> {
    const res = await client.post<AuthResponse>('/auth/patient/register', data);
    return res.data;
  },

  async loginPatient(credentials: {
    email?: string;
    password?: string;
    phone?: string;
    abha_id?: string;
  }): Promise<AuthResponse> {
    const res = await client.post<AuthResponse>('/auth/patient/login', credentials);
    return res.data;
  },

  async getMyProfile(): Promise<Patient> {
    const res = await client.get<Patient>('/patients/me');
    return res.data;
  },

  // ================= HOSPITALS =================
  async getHospitals(): Promise<Hospital[]> {
    const res = await client.get<Hospital[]>('/hospitals');
    return res.data;
  },

  // ================= CONSULTATIONS =================
  async createConsultation(payload: {
    hospital_id: string;
    chief_complaint?: string;
    priority?: string;
    department?: string;
  }): Promise<Consultation> {
    const res = await client.post<Consultation>('/consultations', payload);
    return res.data;
  },

  async getMyConsultations(): Promise<ConsultationListResponse> {
    const res = await client.get<ConsultationListResponse>('/consultations');
    return res.data;
  },

  async getConsultation(id: string): Promise<Consultation> {
    const res = await client.get<Consultation>(`/consultations/${id}`);
    return res.data;
  },

  async recordConsent(
    consultationId: string,
    consentType: string = 'ai_intake_consent'
  ): Promise<ConsentRecord> {
    const res = await client.post<ConsentRecord>(`/consultations/${consultationId}/consent`, {
      consent_type: consentType,
      granted: true,
      version: '1.0',
    });
    return res.data;
  },

  // ================= AI SESSIONS & MESSAGES =================
  async createAISession(consultationId: string, language: string = 'en'): Promise<AISession> {
    const res = await client.post<AISession>('/ai-sessions', {
      consultation_id: consultationId,
      language: language,
    });
    return res.data;
  },

  async getAIMessages(sessionId: string): Promise<AIMessage[]> {
    const res = await client.get<AIMessage[]>(`/ai-sessions/${sessionId}/messages`);
    return res.data;
  },

  async sendAIMessage(
    sessionId: string,
    content: string
  ): Promise<AIInterviewMessageResponse> {
    const dedupeKey = `ai_msg_${sessionId}_${content.trim().slice(0, 32)}`;
    if (pendingRequests.has(dedupeKey)) {
      throw new Error('Please wait, your previous message is still processing.');
    }

    try {
      pendingRequests.add(dedupeKey);
      const res = await client.post<AIInterviewMessageResponse>(
        `/ai-sessions/${sessionId}/messages`,
        { content: content.trim() }
      );
      return res.data;
    } finally {
      pendingRequests.delete(dedupeKey);
    }
  },

  // ================= TRIAGE =================
  async getTriage(consultationId: string): Promise<TriageResult> {
    const res = await client.get<TriageResult>(`/consultations/${consultationId}/triage`);
    return res.data;
  },

  // ================= MEDICAL DOCUMENTS & OCR =================
  async uploadMedicalDocument(
    formData: FormData,
    consultationId?: string
  ): Promise<MedicalDocument> {
    const url = consultationId
      ? `/medical-documents?consultation_id=${consultationId}&process_immediately=true`
      : `/medical-documents?process_immediately=true`;

    const res = await client.post<MedicalDocument>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  async getMedicalDocument(documentId: string): Promise<MedicalDocument> {
    const res = await client.get<MedicalDocument>(`/medical-documents/${documentId}`);
    return res.data;
  },

  async getDocumentExtraction(documentId: string): Promise<StructuredExtraction> {
    const res = await client.get<StructuredExtraction>(
      `/medical-documents/${documentId}/extraction`
    );
    return res.data;
  },

  async getMyDocuments(): Promise<MedicalDocument[]> {
    // Queries all documents belonging to current patient session
    try {
      const res = await client.get<any>('/medical-documents');
      if (Array.isArray(res.data)) {
        return res.data;
      }
      if (res.data && Array.isArray(res.data.items)) {
        return res.data.items;
      }
      return [];
    } catch {
      return [];
    }
  },

  // ================= MEDICAL TIMELINE =================
  async getTimeline(): Promise<TimelineListResponse> {
    const res = await client.get<TimelineListResponse>('/patients/me/timeline');
    return res.data;
  },

  async rebuildTimeline(): Promise<TimelineListResponse> {
    const res = await client.post<TimelineListResponse>('/patients/me/timeline/rebuild');
    return res.data;
  },

  // ================= CLINICAL SUMMARY =================
  async getConsultationSummary(consultationId: string): Promise<ClinicalSummary> {
    const res = await client.get<ClinicalSummary>(`/consultations/${consultationId}/summary`);
    return res.data;
  },
};

export const apiService = api;
