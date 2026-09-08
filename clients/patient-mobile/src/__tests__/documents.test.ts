import { documentApi } from '../api/documents';
import api from '../api/client';

jest.mock('../api/client');

describe('Medical Documents & OCR Extraction Service', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('uploads medical document via multipart/form-data', async () => {
    const mockDoc = {
      id: 'doc-123',
      patient_id: 'pat-1',
      consultation_id: 'cons-123',
      filename: 'prescription.jpg',
      document_type: 'prescription',
      upload_status: 'uploaded',
      ocr_status: 'pending',
      created_at: '2026-09-08T10:10:00Z',
    };

    (api.post as jest.Mock).mockResolvedValueOnce({ data: mockDoc });

    const fileToUpload = {
      uri: 'file:///path/to/prescription.jpg',
      name: 'prescription.jpg',
      type: 'image/jpeg',
    };

    const res = await documentApi.uploadDocument(fileToUpload, 'prescription', 'cons-123');

    expect(api.post).toHaveBeenCalledWith(
      '/medical-documents',
      expect.any(FormData),
      expect.objectContaining({
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    );
    expect(res.id).toBe('doc-123');
    expect(res.document_type).toBe('prescription');
  });

  it('retrieves structured clinical extraction for an uploaded document', async () => {
    const mockExtraction = {
      id: 'ext-456',
      document_id: 'doc-123',
      doctor_name: 'Dr. Sunita Rao',
      hospital_or_clinic_name: 'City Care Hospital',
      diagnosis: ['Type 2 Diabetes Mellitus', 'Hypertension'],
      medications: [
        { name: 'Metformin', dosage: '500mg', frequency: 'twice daily' },
        { name: 'Amlodipine', dosage: '5mg', frequency: 'once daily' },
      ],
      cleaned_text: 'Rx: Metformin 500mg BID, Amlodipine 5mg OD. Dr. Sunita Rao.',
    };

    (api.get as jest.Mock).mockResolvedValueOnce({ data: mockExtraction });

    const res = await documentApi.getExtraction('doc-123');
    expect(api.get).toHaveBeenCalledWith('/medical-documents/doc-123/extraction');
    expect(res.doctor_name).toBe('Dr. Sunita Rao');
    expect(res.medications).toHaveLength(2);
    expect(res.diagnosis).toContain('Hypertension');
  });

  it('triggers asynchronous OCR processing for a document', async () => {
    const mockProcessedDoc = {
      id: 'doc-123',
      upload_status: 'uploaded',
      ocr_status: 'completed',
    };

    (api.post as jest.Mock).mockResolvedValueOnce({ data: mockProcessedDoc });

    const res = await documentApi.processDocument('doc-123');
    expect(api.post).toHaveBeenCalledWith('/medical-documents/doc-123/process');
    expect(res.ocr_status).toBe('completed');
  });
});
