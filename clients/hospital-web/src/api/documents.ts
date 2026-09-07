import { apiClient } from './client';
import { MedicalDocumentListResponse, MedicalDocument, ExtractedDataResponse } from '../types/documents';

export async function listDocuments(consultationId?: string): Promise<MedicalDocumentListResponse> {
  const params: Record<string, string> = {};
  if (consultationId) {
    params.consultation_id = consultationId;
  }
  const response = await apiClient.get<MedicalDocumentListResponse>('/medical-documents', {
    params,
  });
  return response.data;
}

export async function getDocument(documentId: string): Promise<MedicalDocument> {
  const response = await apiClient.get<MedicalDocument>(`/medical-documents/${documentId}`);
  return response.data;
}

export async function getDocumentExtraction(documentId: string): Promise<ExtractedDataResponse> {
  const response = await apiClient.get<ExtractedDataResponse>(`/medical-documents/${documentId}/extraction`);
  return response.data;
}

export function getDocumentFileUrl(documentId: string): string {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
  return `${baseUrl}/medical-documents/${documentId}/file`;
}
