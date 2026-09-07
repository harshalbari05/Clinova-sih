import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Consultation } from '../types/consultation';
import { SummaryResponse } from '../types/summary';
import { TriageResult } from '../types/triage';
import { getConsultation } from '../api/consultations';
import { getSummary, generateSummary, reviewSummary } from '../api/summary';
import { getTriageResult } from '../api/triage';
import { PatientHeader } from '../components/consultation/PatientHeader';
import { RedFlagAlert } from '../components/consultation/RedFlagAlert';
import { SummaryTab } from '../components/consultation/SummaryTab';
import { HistoryTab } from '../components/consultation/HistoryTab';
import { TimelineTab } from '../components/consultation/TimelineTab';
import { DocumentsTab } from '../components/consultation/DocumentsTab';
import { DoctorReviewTab } from '../components/consultation/DoctorReviewTab';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';

type TabType = 'summary' | 'history' | 'timeline' | 'documents' | 'review';

export const ConsultationPage: React.FC = () => {
  const { id: consultationId } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [consultation, setConsultation] = useState<Consultation | null>(null);
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [triage, setTriage] = useState<TriageResult | null>(null);

  const [activeTab, setActiveTab] = useState<TabType>('summary');
  const [loading, setLoading] = useState(true);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    if (!consultationId) return;
    try {
      setLoading(true);
      setError(null);

      // Load consultation details
      const c = await getConsultation(consultationId);
      setConsultation(c);

      // Attempt to load summary (may not exist yet)
      try {
        const s = await getSummary(consultationId);
        setSummary(s);
      } catch {
        setSummary(null);
      }

      // Attempt to load triage
      try {
        const t = await getTriageResult(consultationId);
        setTriage(t);
      } catch {
        setTriage(null);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load consultation case workspace';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [consultationId]);

  // Summary handlers
  const handleEditSummary = async (text: string, notes: string) => {
    if (!consultationId) return;
    try {
      const updated = await reviewSummary(consultationId, {
        action: 'EDITED',
        notes,
        edited_summary: text,
      });
      setSummary(updated);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to save edited summary';
      setError(msg);
      throw err;
    }
  };

  const handleConfirmSummary = async (notes?: string) => {
    if (!consultationId) return;
    try {
      const updated = await reviewSummary(consultationId, {
        action: 'CONFIRMED',
        notes: notes || 'Attested and verified by attending clinician.',
      });
      setSummary(updated);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to confirm summary';
      setError(msg);
      throw err;
    }
  };

  const handleRejectSummary = async (reason: string) => {
    if (!consultationId) return;
    try {
      const updated = await reviewSummary(consultationId, {
        action: 'REJECTED',
        notes: reason,
      });
      setSummary(updated);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to reject summary draft';
      setError(msg);
      throw err;
    }
  };

  const handleRegenerateSummary = async () => {
    if (!consultationId) return;
    try {
      setSummaryLoading(true);
      setError(null);
      const generated = await generateSummary(consultationId);
      setSummary(generated);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to generate clinical summary draft';
      setError(msg);
    } finally {
      setSummaryLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner text="Opening consultation workspace..." />;
  }

  if (error && !consultation) {
    return (
      <div className="space-y-4">
        <ErrorAlert message={error} />
        <button
          onClick={() => navigate('/queue')}
          className="px-4 py-2 bg-primary text-white rounded-xl text-xs font-bold"
        >
          Return to OPD Queue
        </button>
      </div>
    );
  }

  if (!consultation) {
    return (
      <div className="p-12 text-center bg-white rounded-2xl border border-slate-200">
        <p className="text-sm font-bold text-slate-700">Consultation Not Found</p>
        <button
          onClick={() => navigate('/queue')}
          className="mt-4 px-4 py-2 bg-primary text-white rounded-xl text-xs font-bold"
        >
          Return to Queue
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Patient Header */}
      <PatientHeader consultation={consultation} tokenNumber={1} />

      {/* Red-Flag Urgent Clinical Alert */}
      <RedFlagAlert triage={triage} />

      {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

      {/* Navigation Tabs */}
      <div className="border-b border-slate-200 bg-white rounded-t-2xl px-4 pt-3 flex items-center gap-2 overflow-x-auto">
        {[
          {
            id: 'summary' as TabType,
            label: 'AI Clinical Summary',
            icon: 'auto_awesome',
            badge: summary?.status,
          },
          {
            id: 'history' as TabType,
            label: 'Clinical Intake History',
            icon: 'history_edu',
          },
          {
            id: 'timeline' as TabType,
            label: 'Medical Timeline',
            icon: 'timeline',
          },
          {
            id: 'documents' as TabType,
            label: 'Diagnostic Documents & OCR',
            icon: 'biotech',
          },
          {
            id: 'review' as TabType,
            label: 'Physician Exam & Notes',
            icon: 'stethoscope',
            badge: summary?.status === 'confirmed' ? 'verified' : undefined,
          },
        ].map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 text-xs font-bold border-b-2 whitespace-nowrap transition-all ${
                isActive
                  ? 'border-primary text-primary bg-primary/5 rounded-t-lg'
                  : 'border-transparent text-slate-600 hover:text-slate-900 hover:border-slate-300'
              }`}
            >
              <span className="material-symbols-outlined text-base">{tab.icon}</span>
              <span>{tab.label}</span>
              {tab.badge && (
                <span
                  className={`text-[9px] font-black uppercase px-1.5 py-0.5 rounded-full ${
                    tab.badge === 'confirmed' || tab.badge === 'verified'
                      ? 'bg-emerald-100 text-emerald-800'
                      : tab.badge === 'rejected'
                      ? 'bg-rose-100 text-rose-800'
                      : 'bg-amber-100 text-amber-800'
                  }`}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Panels */}
      <div className="bg-white rounded-b-2xl border border-slate-200 border-t-0 p-6 shadow-sm">
        {activeTab === 'summary' && (
          <SummaryTab
            summary={summary}
            isLoading={summaryLoading}
            onEdit={handleEditSummary}
            onConfirm={handleConfirmSummary}
            onReject={handleRejectSummary}
            onRegenerate={handleRegenerateSummary}
          />
        )}

        {activeTab === 'history' && (
          <HistoryTab consultationId={consultation.id} />
        )}

        {activeTab === 'timeline' && (
          <TimelineTab consultationId={consultation.id} />
        )}

        {activeTab === 'documents' && (
          <DocumentsTab consultationId={consultation.id} />
        )}

        {activeTab === 'review' && (
          <DoctorReviewTab
            consultation={consultation}
            summary={summary}
            onOpenConfirmModal={() => setActiveTab('summary')}
            onOpenEditModal={() => setActiveTab('summary')}
          />
        )}
      </div>
    </div>
  );
};
