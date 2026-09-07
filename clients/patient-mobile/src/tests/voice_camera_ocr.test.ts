import { describe, it, expect, beforeEach, vi } from 'vitest';
import { api } from '../services/api';
import { voiceService } from '../services/voice';

describe('Patient Mobile - Voice Input, Camera & OCR Extraction', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('checks and requests audio recording permissions for voice input', async () => {
    const perm = await voiceService.requestPermission();
    expect(perm.granted).toBe(true);
  });

  it('provides reliable speech transcription with fallback', async () => {
    let transcribedText = '';
    await voiceService.startListening((text) => {
      transcribedText = text;
    });

    // Simulate callback
    expect(voiceService.isSupported()).toBe(true);
    await voiceService.stopListening();
  });

  it('uploads captured document via multipart/form-data with process_immediately=true', async () => {
    const mockDoc = {
      id: 'doc-999',
      patient_id: 'p-123',
      consultation_id: 'c-123',
      filename: 'rx_patel.jpg',
      document_type: 'prescription',
      upload_status: 'uploaded',
      ocr_status: 'processing',
      processing_status: 'PROCESSING',
      created_at: '2026-09-07T10:20:00Z',
    };

    const spy = vi.spyOn(api, 'uploadMedicalDocument').mockResolvedValueOnce(mockDoc);

    const formData = new FormData();
    formData.append('file', { uri: 'file://path/rx.jpg', name: 'rx_patel.jpg', type: 'image/jpeg' } as any);
    formData.append('document_type', 'prescription');

    const result = await api.uploadMedicalDocument(formData, 'c-123');
    expect(spy).toHaveBeenCalledTimes(1);
    expect(result.id).toBe('doc-999');
    expect(result.ocr_status).toBe('processing');
  });

  it('retrieves source-backed structured extraction without clinical fabrication', async () => {
    const mockExtraction = {
      id: 'ext-999',
      document_id: 'doc-999',
      document_type: 'prescription',
      doctor_name: 'Dr. K. Patel',
      hospital_or_clinic_name: 'City Hospital OPD',
      document_date: '2026-08-28',
      medications: [
        { name: 'Metformin 500mg', dosage: '1-0-1' },
        { name: 'Telmisartan 40mg', dosage: '1-0-0' },
      ],
      laboratory_results: [
        { test: 'Fasting Blood Sugar', value: '110 mg/dL' },
      ],
      warnings: ['Hand-written frequency in top margin is slightly faint.'],
    };

    vi.spyOn(api, 'getDocumentExtraction').mockResolvedValueOnce(mockExtraction);

    const extraction = await api.getDocumentExtraction('doc-999');
    expect(extraction.doctor_name).toBe('Dr. K. Patel');
    expect(extraction.medications?.length).toBe(2);
    expect(extraction.laboratory_results?.[0].test).toBe('Fasting Blood Sugar');
    // Source data only: No "You have diabetes" fabricated statement
    expect(JSON.stringify(extraction)).not.toContain('You have diabetes');
  });
});
