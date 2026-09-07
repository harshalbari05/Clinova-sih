import api from './client';
import { MedicalDocument, StructuredExtraction } from '../types';

export const documentApi = {
  async uploadDocument(
    file: File,
    documentType: string = 'other',
    consultationId?: string
  ): Promise<MedicalDocument> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);
    if (consultationId) {
      formData.append('consultation_id', consultationId);
    }
    formData.append('process_immediately', 'true');

    const res = await api.post<MedicalDocument>('/medical-documents', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  async processDocument(documentId: string): Promise<MedicalDocument> {
    const res = await api.post<MedicalDocument>(`/medical-documents/${documentId}/process`);
    return res.data;
  },

  async getDocument(documentId: string): Promise<MedicalDocument> {
    const res = await api.get<MedicalDocument>(`/medical-documents/${documentId}`);
    return res.data;
  },

  async getExtraction(documentId: string): Promise<StructuredExtraction> {
    const res = await api.get<StructuredExtraction>(`/medical-documents/${documentId}/extraction`);
    return res.data;
  },

  async listDocuments(consultationId?: string): Promise<{ items: MedicalDocument[]; total: number }> {
    const params: Record<string, any> = {};
    if (consultationId) params.consultation_id = consultationId;
    const res = await api.get<{ items: MedicalDocument[]; total: number }>('/medical-documents', {
      params,
    });
    return res.data;
  },
};
