import React, { useState, useEffect } from 'react';
import { MedicalDocument, ExtractedDataResponse } from '../../types/documents';
import { listDocuments, getDocumentExtraction, getDocumentFileUrl } from '../../api/documents';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorAlert } from '../common/ErrorAlert';
import { Modal } from '../common/Modal';

interface DocumentsTabProps {
  consultationId: string;
}

export const DocumentsTab: React.FC<DocumentsTabProps> = ({ consultationId }) => {
  const [documents, setDocuments] = useState<MedicalDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Extraction Inspection State
  const [selectedDoc, setSelectedDoc] = useState<MedicalDocument | null>(null);
  const [extraction, setExtraction] = useState<ExtractedDataResponse | null>(null);
  const [extractionLoading, setExtractionLoading] = useState(false);
  const [extractionError, setExtractionError] = useState<string | null>(null);
  const [activeSubTab, setActiveSubTab] = useState<'structured' | 'ocr'>('structured');

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await listDocuments(consultationId);
      setDocuments(res.items || []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load medical documents';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (consultationId) {
      fetchDocuments();
    }
  }, [consultationId]);

  const handleInspect = async (doc: MedicalDocument) => {
    setSelectedDoc(doc);
    setActiveSubTab('structured');
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

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (loading) {
    return <LoadingSpinner text="Loading medical documents & lab reports..." />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold text-slate-900 tracking-tight">Attached Medical Documents & Reports</h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Original patient uploads with automated OCR parsing and structured clinical entity extraction.
          </p>
        </div>
        <button
          onClick={fetchDocuments}
          className="text-xs font-semibold text-primary hover:text-primary-dark flex items-center gap-1.5 px-3 py-1.5 bg-primary/5 rounded-lg transition-colors"
        >
          <span className="material-symbols-outlined text-sm">refresh</span>
          Refresh Documents
        </button>
      </div>

      {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

      {documents.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-xl border border-slate-200 shadow-sm">
          <span className="material-symbols-outlined text-4xl text-slate-300 mb-2">folder_open</span>
          <p className="text-sm font-semibold text-slate-700">No Attached Medical Records</p>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
            The patient has not attached external diagnostic reports or lab investigations to this consultation session.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {documents.map((doc) => {
            const isCompleted = doc.processing_state === 'completed';
            const isProcessing = doc.processing_state === 'processing';
            const isFailed = doc.processing_state === 'failed';

            return (
              <div
                key={doc.id}
                className="bg-white rounded-xl border border-slate-200 hover:border-primary/40 p-5 transition-all shadow-sm hover:shadow-md flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-teal-50 border border-teal-100 flex items-center justify-center text-primary flex-shrink-0">
                        <span className="material-symbols-outlined text-xl">
                          {doc.document_type?.toLowerCase().includes('lab') ? 'biotech' : 'description'}
                        </span>
                      </div>
                      <div className="min-w-0">
                        <h4 className="text-sm font-bold text-slate-900 truncate" title={doc.original_filename}>
                          {doc.original_filename}
                        </h4>
                        <div className="flex items-center gap-2 mt-0.5 text-xs text-slate-500">
                          <span className="uppercase font-semibold tracking-wider text-[10px] text-slate-400">
                            {doc.document_type || 'General Record'}
                          </span>
                          <span>•</span>
                          <span>{formatFileSize(doc.file_size_bytes)}</span>
                        </div>
                      </div>
                    </div>

                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                        isCompleted
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : isProcessing
                          ? 'bg-amber-50 text-amber-700 border border-amber-200 animate-pulse'
                          : isFailed
                          ? 'bg-rose-50 text-rose-700 border border-rose-200'
                          : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      {doc.processing_state}
                    </span>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-100 grid grid-cols-2 gap-2 text-xs text-slate-600">
                    <div>
                      <span className="text-[11px] text-slate-400 block">Uploaded On</span>
                      <span className="font-medium text-slate-700">
                        {new Date(doc.created_at).toLocaleDateString(undefined, {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                        })}
                      </span>
                    </div>
                    <div>
                      <span className="text-[11px] text-slate-400 block">AI & OCR Parsing</span>
                      <div className="flex items-center gap-1.5 mt-0.5">
                        <span
                          className={`w-2 h-2 rounded-full ${
                            doc.ocr_extracted ? 'bg-emerald-500' : 'bg-slate-300'
                          }`}
                        />
                        <span className="text-[11px] font-medium text-slate-700">
                          {doc.ocr_extracted ? 'Parsed & Extracted' : 'Pending'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                  <a
                    href={getDocumentFileUrl(doc.id)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors"
                  >
                    <span className="material-symbols-outlined text-sm">visibility</span>
                    View File
                  </a>

                  <button
                    onClick={() => handleInspect(doc)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-white bg-primary hover:bg-primary-dark shadow-sm transition-colors"
                  >
                    <span className="material-symbols-outlined text-sm">troubleshoot</span>
                    Inspect Extractions
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Extraction Inspection Modal */}
      {selectedDoc && (
        <Modal
          isOpen={true}
          onClose={() => {
            setSelectedDoc(null);
            setExtraction(null);
          }}
          title={`Document Extraction: ${selectedDoc.original_filename}`}
          maxWidth="max-w-4xl"
        >
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setActiveSubTab('structured')}
                  className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors flex items-center gap-1.5 ${
                    activeSubTab === 'structured'
                      ? 'bg-primary text-white'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <span className="material-symbols-outlined text-sm">view_timeline</span>
                  Structured Clinical Findings
                </button>
                <button
                  onClick={() => setActiveSubTab('ocr')}
                  className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors flex items-center gap-1.5 ${
                    activeSubTab === 'ocr'
                      ? 'bg-primary text-white'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <span className="material-symbols-outlined text-sm">notes</span>
                  Raw OCR Text
                </button>
              </div>

              <a
                href={getDocumentFileUrl(selectedDoc.id)}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
              >
                <span className="material-symbols-outlined text-sm">open_in_new</span>
                Open Original Document
              </a>
            </div>

            {extractionLoading ? (
              <LoadingSpinner text="Retrieving structured OCR and clinical entities..." />
            ) : extractionError ? (
              <ErrorAlert message={extractionError} />
            ) : !extraction ? (
              <div className="p-8 text-center text-slate-500 text-xs">No extraction data available.</div>
            ) : activeSubTab === 'ocr' ? (
              <div className="space-y-3">
                <div className="p-4 bg-slate-900 text-slate-100 font-mono text-xs rounded-xl overflow-x-auto max-h-96 whitespace-pre-wrap leading-relaxed">
                  {extraction.ocr_text || 'No raw OCR text available.'}
                </div>
                <p className="text-[11px] text-slate-400">
                  Extracted via Optical Character Recognition pipeline. Text is preserved verbatim for provenance.
                </p>
              </div>
            ) : (
              <div className="space-y-6 max-h-[60vh] overflow-y-auto pr-1">
                {/* Document Metadata banner */}
                {extraction.structured_data?.hospital_name || extraction.structured_data?.doctor_name ? (
                  <div className="p-3 bg-teal-50 border border-teal-100 rounded-lg flex items-center justify-between text-xs text-slate-700">
                    {extraction.structured_data.hospital_name && (
                      <div>
                        <span className="text-[11px] text-slate-400 block font-medium">Origin Hospital/Lab</span>
                        <span className="font-semibold text-slate-900">{extraction.structured_data.hospital_name}</span>
                      </div>
                    )}
                    {extraction.structured_data.doctor_name && (
                      <div>
                        <span className="text-[11px] text-slate-400 block font-medium">Referring Practitioner</span>
                        <span className="font-semibold text-slate-900">{extraction.structured_data.doctor_name}</span>
                      </div>
                    )}
                    {extraction.structured_data.report_date && (
                      <div>
                        <span className="text-[11px] text-slate-400 block font-medium">Report Date</span>
                        <span className="font-semibold text-slate-900">{extraction.structured_data.report_date}</span>
                      </div>
                    )}
                  </div>
                ) : null}

                {/* Lab Results */}
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-base text-primary">biotech</span>
                    Extracted Lab Investigations & Biomarkers
                  </h4>
                  {extraction.structured_data?.lab_results && extraction.structured_data.lab_results.length > 0 ? (
                    <div className="border border-slate-200 rounded-xl overflow-hidden shadow-sm">
                      <table className="w-full text-left text-xs border-collapse">
                        <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold">
                          <tr>
                            <th className="px-3.5 py-2.5">Test / Biomarker</th>
                            <th className="px-3.5 py-2.5">Result</th>
                            <th className="px-3.5 py-2.5">Unit</th>
                            <th className="px-3.5 py-2.5">Reference Range</th>
                            <th className="px-3.5 py-2.5">Flag</th>
                            <th className="px-3.5 py-2.5">Evidence</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {extraction.structured_data.lab_results.map((lab, idx) => {
                            const isAbnormal = lab.flag && lab.flag.toLowerCase() !== 'normal';
                            return (
                              <tr key={idx} className={isAbnormal ? 'bg-amber-50/40' : 'hover:bg-slate-50/60'}>
                                <td className="px-3.5 py-2.5 font-bold text-slate-900">{lab.test_name}</td>
                                <td className="px-3.5 py-2.5 font-bold text-slate-800">{lab.result_value}</td>
                                <td className="px-3.5 py-2.5 text-slate-500">{lab.unit || '—'}</td>
                                <td className="px-3.5 py-2.5 text-slate-500">{lab.reference_range || '—'}</td>
                                <td className="px-3.5 py-2.5">
                                  {lab.flag ? (
                                    <span
                                      className={`px-2 py-0.5 text-[10px] font-bold rounded-full uppercase ${
                                        isAbnormal
                                          ? 'bg-rose-100 text-rose-800 border border-rose-200'
                                          : 'bg-emerald-100 text-emerald-800'
                                      }`}
                                    >
                                      {lab.flag}
                                    </span>
                                  ) : (
                                    <span className="text-slate-400">—</span>
                                  )}
                                </td>
                                <td className="px-3.5 py-2.5 text-slate-500 italic max-w-xs truncate" title={lab.evidence || ''}>
                                  {lab.evidence ? `"${lab.evidence}"` : '—'}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="text-xs text-slate-400 italic bg-slate-50 p-3 rounded-lg border border-slate-100">
                      No specific lab values extracted from this document.
                    </p>
                  )}
                </div>

                {/* Medications */}
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-base text-primary">prescriptions</span>
                    Extracted Prescribed Medications
                  </h4>
                  {extraction.structured_data?.medications && extraction.structured_data.medications.length > 0 ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {extraction.structured_data.medications.map((med, idx) => (
                        <div key={idx} className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-sm text-slate-900">{med.name}</span>
                            {med.dosage && (
                              <span className="text-xs font-medium text-slate-600 bg-white px-2 py-0.5 rounded border border-slate-200">
                                {med.dosage}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-3 mt-1.5 text-xs text-slate-500">
                            {med.frequency && <span>Freq: {med.frequency}</span>}
                            {med.duration && <span>Duration: {med.duration}</span>}
                          </div>
                          {med.evidence && (
                            <p className="text-[11px] text-slate-400 italic mt-2 pt-2 border-t border-slate-200 truncate" title={med.evidence}>
                              Evidence: "{med.evidence}"
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-400 italic bg-slate-50 p-3 rounded-lg border border-slate-100">
                      No medication regimens identified.
                    </p>
                  )}
                </div>

                {/* Diagnoses */}
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-base text-primary">diagnosis</span>
                    Extracted Diagnoses / Conditions
                  </h4>
                  {extraction.structured_data?.diagnoses && extraction.structured_data.diagnoses.length > 0 ? (
                    <div className="space-y-2">
                      {extraction.structured_data.diagnoses.map((diag, idx) => (
                        <div key={idx} className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between">
                          <div>
                            <span className="font-bold text-xs text-slate-900">{diag.diagnosis}</span>
                            {diag.evidence && (
                              <p className="text-[11px] text-slate-400 italic mt-0.5">"{diag.evidence}"</p>
                            )}
                          </div>
                          {diag.status && (
                            <span className="text-[10px] font-bold uppercase px-2 py-0.5 bg-slate-200 text-slate-700 rounded-full">
                              {diag.status}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-400 italic bg-slate-50 p-3 rounded-lg border border-slate-100">
                      No formal diagnoses listed in document.
                    </p>
                  )}
                </div>

                {/* Vital signs */}
                {extraction.structured_data?.vital_signs && Object.keys(extraction.structured_data.vital_signs).length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-base text-primary">vital_signs</span>
                      Recorded Vitals
                    </h4>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                      {Object.entries(extraction.structured_data.vital_signs).map(([key, val]) => (
                        <div key={key} className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-center">
                          <span className="text-[10px] uppercase font-bold text-slate-400 block">{key}</span>
                          <span className="text-sm font-bold text-slate-800">{String(val)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Disclaimer */}
                {extraction.structured_data?.disclaimer && (
                  <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-start gap-2.5">
                    <span className="material-symbols-outlined text-amber-600 text-base mt-0.5 flex-shrink-0">
                      warning
                    </span>
                    <p className="leading-relaxed">{extraction.structured_data.disclaimer}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
};
