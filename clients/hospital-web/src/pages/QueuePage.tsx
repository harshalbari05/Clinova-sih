import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Consultation } from '../types/consultation';
import { listConsultations } from '../api/consultations';
import { QueueTable } from '../components/queue/QueueTable';
import { QueueMetrics } from '../components/queue/QueueMetrics';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';

export const QueuePage: React.FC = () => {
  const navigate = useNavigate();
  const [consultations, setConsultations] = useState<Consultation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [activeStatus, setActiveStatus] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const fetchQueue = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await listConsultations({
        status: activeStatus !== 'all' ? activeStatus : undefined,
        limit: 100,
      });
      setConsultations(res.items || []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to retrieve OPD queue';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, [activeStatus]);

  const filteredConsultations = consultations.filter((c) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    const idMatch = c.patient_id.toLowerCase().includes(q) || c.id.toLowerCase().includes(q);
    const complaintMatch = c.chief_complaint ? c.chief_complaint.toLowerCase().includes(q) : false;
    return idMatch || complaintMatch;
  });

  const waitingCount = consultations.filter((c) => c.status === 'initiated').length;
  const inProgressCount = consultations.filter((c) => c.status === 'in_progress').length;
  const completedCount = consultations.filter((c) => c.status === 'completed' || c.status === 'reviewed').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">OPD Patient Queue</h1>
          <p className="text-xs text-slate-500 mt-1">
            Real-time outpatient consultation flow, automated token progression, and triage prioritization.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchQueue}
            className="inline-flex items-center gap-1.5 px-3 py-2 bg-white border border-slate-200 hover:border-slate-300 text-slate-700 text-xs font-semibold rounded-xl transition-colors shadow-sm"
          >
            <span className="material-symbols-outlined text-sm">refresh</span>
            Refresh
          </button>
        </div>
      </div>

      {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

      {/* Metrics */}
      <QueueMetrics
        total={consultations.length}
        waiting={waitingCount}
        inProgress={inProgressCount}
        completed={completedCount}
      />

      {/* Filter & Search Toolbar */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          {/* Status Tabs */}
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl overflow-x-auto text-xs font-bold">
            {[
              { id: 'all', label: 'All Cases' },
              { id: 'initiated', label: 'Waiting / Initiated' },
              { id: 'in_progress', label: 'In Consultation' },
              { id: 'completed', label: 'Completed' },
              { id: 'reviewed', label: 'Doctor Reviewed' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveStatus(tab.id)}
                className={`px-3 py-1.5 rounded-lg whitespace-nowrap transition-all ${
                  activeStatus === tab.id
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Search Box */}
          <div className="relative min-w-[240px]">
            <span className="material-symbols-outlined absolute left-3 top-2 text-slate-400 text-base">
              search
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search patient ID or complaint..."
              className="w-full pl-9 pr-3 py-1.5 text-xs border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary text-slate-900"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 top-2 text-slate-400 hover:text-slate-600"
              >
                <span className="material-symbols-outlined text-xs">close</span>
              </button>
            )}
          </div>
        </div>

        {/* Queue Table */}
        {loading ? (
          <LoadingSpinner text="Refreshing OPD consultation queue..." />
        ) : (
          <QueueTable
            consultations={filteredConsultations}
            onSelectConsultation={(c: Consultation) => navigate(`/consultation/${c.id}`)}
          />
        )}
      </div>
    </div>
  );
};
