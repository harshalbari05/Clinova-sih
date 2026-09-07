import React, { useState, useEffect } from 'react';
import { MedicalDocument, ExtractedDataResponse } from '../types/documents';
import { listDocuments, getDocumentExtraction, getDocumentFileUrl } from '../api/documents';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { Modal } from '../components/common/Modal';

export const DocumentsPage: React.FC = () => {
  const [documents, setDocuments] = useState<MedicalDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Extraction Inspection
  const [selectedDoc, setSelectedDoc] = useState<MedicalDocument | null>(null);
  const [extraction, setExtraction] = useState<ExtractedDataResponse | null>(null);
  const [extractionLoading, setExtractionLoading] = useState(false);
  const [extractionError, setExtractionError] = useState<string | null>(null);

  const fetchDocs = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await listDocuments();
      setDocuments(res.items || []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to retrieve documents';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const handleInspect = async (doc: MedicalDocument) => {
    setSelectedDoc(doc);
    setExtractionLoading(true);
    setExtractionError(null);
    try {
      const data = await getDocumentExtraction(doc.id);
      setExtraction(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to retrieve OCR / structured extractions';
      setExtractionError(msg);
    } finally {
      setExtractionLoading(false);
    }
  };

  const filteredDocs = documents.filter((d) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      d.original_filename.toLowerCase().includes(q) ||
      d.document_type.toLowerCase().includes(q) ||
      d.patient_id.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Diagnostic Records & OCR</h1>
          <p className="text-xs text-slate-500 mt-1">
            Browse uploaded medical investigations, lab biomarkers, and structured extraction records.
          </p>
        </div>

        <button
          onClick={fetchDocs}
          className="inline-flex items-center gap-1.5 px-3 py-2 bg-white border border-slate-200 text-slate-700 text-xs font-semibold rounded-xl hover:border-slate-300 shadow-sm"
        >
          <span className="material-symbols-outlined text-sm">refresh</span>
          Refresh
        </button>
      </div>

      {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

      {/* Search Bar */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm">
        <div className="relative max-w-md">
          <span className="material-symbols-outlined absolute left-3 top-2.5 text-slate-400 text-base">
            search
          </span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by filename, document type, or patient ID..."
            className="w-full pl-9 pr-3 py-2 text-xs border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary text-slate-900"
          />
        </div>
      </div>

      {/* Documents Grid / Table */}
      {loading ? (
        <LoadingSpinner text="Loading repository records..." />
      ) : filteredDocs.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center shadow-sm">
          <span className="material-symbols-outlined text-4xl text-slate-300 mb-2">folder_open</span>
          <p className="text-sm font-bold text-slate-700">No Diagnostic Documents Found</p>
          <p className="text-xs text-slate-400 mt-1">
            Attached medical records will appear here as patients upload laboratory or diagnostic files.
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold">
              <tr>
                <th className="px-4 py-3">Document Name</th>
                <th className="px-4 py-3">Patient ID</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Processing State</th>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredDocs.map((doc) => (
                <tr key={doc.id} className="hover:bg-slate-50/60 transition-colors">
                  <td className="px-4 py-3.5 font-bold text-slate-900">
                    <div className="flex items-center gap-2">
                      <span className="material-symbols-outlined text-primary text-lg">description</span>
                      <span className="truncate max-w-xs">{doc.original_filename}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3.5 font-mono text-slate-600">#{doc.patient_id.slice(0, 8)}</td>
                  <td className="px-4 py-3.5 uppercase font-medium text-slate-500 text-[11px]">
                    {doc.document_type}
                  </td>
                  <td className="px-4 py-3.5">
                    <span
                      className={`px-2 py-0.5 text-[10px] font-bold rounded-full uppercase ${
                        doc.processing_state === 'completed'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : doc.processing_state === 'processing'
                          ? 'bg-amber-50 text-amber-700 border border-amber-200'
                          : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      {doc.processing_state}
                    </span>
                  </td>
                  <td className="px-4 py-3.5 text-slate-500">
                    {new Date(doc.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3.5 text-right space-x-2">
                    <a
                      href={getDocumentFileUrl(doc.id)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                    >
                      <span className="material-symbols-outlined text-xs">visibility</span>
                      File
                    </a>
                    <button
                      onClick={() => handleInspect(doc)}
                      className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-white bg-primary hover:bg-primary-dark rounded-lg transition-colors"
                    >
                      <span className="material-symbols-outlined text-xs">troubleshoot</span>
                      Extractions
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Inspection Modal */}
      {selectedDoc && (
        <Modal
          isOpen={true}
          onClose={() => {
            setSelectedDoc(null);
            setExtraction(null);
          }}
          title={`Document: ${selectedDoc.original_filename}`}
          maxWidth="max-w-3xl"
        >
          {extractionLoading ? (
            <LoadingSpinner text="Fetching OCR and structured laboratory extractions..." />
          ) : extractionError ? (
            <ErrorAlert message={extractionError} />
          ) : !extraction ? (
            <p className="text-xs text-slate-500">No extractions found.</p>
          ) : (
            <div className="space-y-4 max-h-[60vh] overflow-y-auto">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between text-xs">
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Extraction Status</span>
                  <span className="font-bold text-slate-900 uppercase">{extraction.extraction_status}</span>
                </div>
                <a
                  href={getDocumentFileUrl(selectedDoc.id)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline font-bold"
                >
                  View Original PDF/Image
                </a>
              </div>

              {extraction.structured_data?.lab_results && extraction.structured_data.lab_results.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                    Lab Biomarkers
                  </h4>
                  <div className="border border-slate-200 rounded-xl overflow-hidden">
                    <table className="w-full text-xs text-left">
                      <thead className="bg-slate-50 border-b border-slate-200 text-slate-500">
                        <tr>
                          <th className="p-2.5">Test</th>
                          <th className="p-2.5">Result</th>
                          <th className="p-2.5">Reference</th>
                          <th className="p-2.5">Flag</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {extraction.structured_data.lab_results.map((lab, idx) => (
                          <tr key={idx}>
                            <td className="p-2.5 font-bold text-slate-800">{lab.test_name}</td>
                            <td className="p-2.5 font-semibold text-slate-700">
                              {lab.result_value} {lab.unit}
                            </td>
                            <td className="p-2.5 text-slate-500">{lab.reference_range || '—'}</td>
                            <td className="p-2.5">
                              {lab.flag ? (
                                <span className="px-1.5 py-0.5 text-[9px] font-bold rounded bg-rose-100 text-rose-800">
                                  {lab.flag}
                                </span>
                              ) : (
                                <span className="text-slate-400">—</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {extraction.ocr_text && (
                <div>
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Raw OCR Text</h4>
                  <pre className="p-3 bg-slate-900 text-slate-200 text-xs font-mono rounded-xl max-h-48 overflow-y-auto whitespace-pre-wrap">
                    {extraction.ocr_text}
                  </pre>
                </div>
              )}
            </div>
          )}
        </Modal>
      )}
    </div>
  );
};
