import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Consultation } from '../types/consultation';
import { DepartmentQueueResponse } from '../types/reception';
import { listConsultations } from '../api/consultations';
import {
  getDepartments,
  getDepartmentQueue,
  advanceDepartmentQueue,
} from '../api/reception';
import { QueueTable } from '../components/queue/QueueTable';
import { QueueMetrics } from '../components/queue/QueueMetrics';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { useOptionalAuth } from '../context/AuthContext';

const DEFAULT_DEPARTMENTS = [
  'General Medicine',
  'Orthopedics',
  'Pediatrics',
  'ENT',
  'Cardiology',
  'Dermatology',
];

export const QueuePage: React.FC = () => {
  const navigate = useNavigate();
  const auth = useOptionalAuth();
  const isReceptionist = auth?.hospitalRole === 'receptionist';

  // Mode: 'department' (SIH Step 3 requirement) or 'all' (classic full list)
  const [viewMode, setViewMode] = useState<'department' | 'all'>('department');

  // Department Queue state
  const [departments, setDepartments] = useState<string[]>(DEFAULT_DEPARTMENTS);
  const [selectedDepartment, setSelectedDepartment] = useState<string>('General Medicine');
  const [departmentQueue, setDepartmentQueue] = useState<DepartmentQueueResponse | null>(null);
  const [advancing, setAdvancing] = useState(false);
  const [advanceMessage, setAdvanceMessage] = useState<string | null>(null);

  // All Consultations state
  const [consultations, setConsultations] = useState<Consultation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters for 'all' mode
  const [activeStatus, setActiveStatus] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Load available departments
  useEffect(() => {
    async function loadDepts() {
      try {
        const list = await getDepartments();
        if (list && list.length > 0) {
          setDepartments(list);
        }
      } catch {
        // Keep defaults
      }
    }
    loadDepts();
  }, []);

  // Fetch department queue
  const fetchDepartmentQueueData = useCallback(async () => {
    try {
      setError(null);
      const queueData = await getDepartmentQueue(selectedDepartment);
      setDepartmentQueue(queueData);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to retrieve department queue';
      setError(msg);
    }
  }, [selectedDepartment]);

  // Fetch full consultation list (when in 'all' view)
  const fetchConsultationsList = useCallback(async () => {
    try {
      setError(null);
      const res = await listConsultations({
        status: activeStatus !== 'all' ? activeStatus : undefined,
        limit: 100,
      });
      setConsultations(res.items || []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to retrieve OPD cases';
      setError(msg);
    }
  }, [activeStatus]);

  // Main loader
  const refreshCurrentView = useCallback(async () => {
    setLoading(true);
    if (viewMode === 'department') {
      await fetchDepartmentQueueData();
    } else {
      await fetchConsultationsList();
    }
    setLoading(false);
  }, [viewMode, fetchDepartmentQueueData, fetchConsultationsList]);

  // Initial load and on view / dept change
  useEffect(() => {
    refreshCurrentView();
  }, [refreshCurrentView]);

  // Polling every 6 seconds to reflect real-time patient registrations and queue progression
  useEffect(() => {
    const interval = setInterval(() => {
      if (viewMode === 'department') {
        fetchDepartmentQueueData();
      }
    }, 6000);
    return () => clearInterval(interval);
  }, [viewMode, fetchDepartmentQueueData]);

  // Advance queue handler (Call Next Patient)
  const handleAdvanceQueue = async () => {
    try {
      setAdvancing(true);
      setError(null);
      setAdvanceMessage(null);
      const result = await advanceDepartmentQueue(selectedDepartment);
      setAdvanceMessage(result.message);
      await fetchDepartmentQueueData();
      setTimeout(() => setAdvanceMessage(null), 5000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to advance queue';
      setError(msg);
    } finally {
      setAdvancing(false);
    }
  };

  const waitingEntries = departmentQueue?.entries.filter((e) => e.status === 'waiting') || [];
  const servingEntry = departmentQueue?.entries.find((e) => e.status === 'in_progress');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">OPD Department Queue</h1>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-primary/10 text-primary border border-primary/20">
              Department-Scoped
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Real-time OPD token progression by department. Patient consultations are routed by department, not assigned to individual doctors.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Mode Switcher */}
          <div className="flex items-center bg-surface-container-low p-1 rounded-xl border border-outline-variant/30 text-xs font-bold">
            <button
              onClick={() => setViewMode('department')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                viewMode === 'department'
                  ? 'bg-primary text-on-primary shadow-xs'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              Department Tokens
            </button>
            <button
              onClick={() => setViewMode('all')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                viewMode === 'all'
                  ? 'bg-primary text-on-primary shadow-xs'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              All Hospital Cases
            </button>
          </div>

          <button
            onClick={() => navigate('/registration')}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-primary hover:bg-primary-container text-on-primary text-xs font-bold rounded-xl transition-colors shadow-xs"
          >
            <span className="material-symbols-outlined text-[16px]">how_to_reg</span>
            <span>Register Patient</span>
          </button>
          <button
            onClick={refreshCurrentView}
            className="inline-flex items-center gap-1.5 px-3 py-2 bg-white border border-slate-200 hover:border-slate-300 text-slate-700 text-xs font-semibold rounded-xl transition-colors shadow-sm"
          >
            <span className="material-symbols-outlined text-sm">refresh</span>
            Refresh
          </button>
        </div>
      </div>

      {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

      {advanceMessage && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center justify-between text-xs text-emerald-900 font-semibold shadow-xs animate-fadeIn">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-emerald-600 text-[20px]">campaign</span>
            <span>{advanceMessage}</span>
          </div>
          <button onClick={() => setAdvanceMessage(null)} className="text-emerald-700 hover:text-emerald-900">
            <span className="material-symbols-outlined text-[16px]">close</span>
          </button>
        </div>
      )}

      {/* DEPARTMENT TOKENS VIEW */}
      {viewMode === 'department' && (
        <div className="space-y-6">
          {/* Department Selector Tabs */}
          <div className="bg-surface-container-lowest rounded-2xl border border-outline-variant/30 p-2 shadow-xs">
            <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
              {departments.map((dept) => {
                const isSelected = selectedDepartment === dept;
                return (
                  <button
                    key={dept}
                    onClick={() => setSelectedDepartment(dept)}
                    className={`px-4 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all flex items-center gap-2 ${
                      isSelected
                        ? 'bg-primary text-on-primary shadow-sm'
                        : 'bg-surface-container-low text-on-surface-variant hover:text-on-surface hover:bg-surface-container'
                    }`}
                  >
                    <span className="material-symbols-outlined text-[16px]">
                      {dept.includes('General')
                        ? 'medical_services'
                        : dept.includes('Ortho')
                        ? 'accessible'
                        : dept.includes('Pedia')
                        ? 'child_care'
                        : dept.includes('Cardio')
                        ? 'cardiology'
                        : 'local_hospital'}
                    </span>
                    <span>{dept}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Now Serving & Waiting Tokens Hero Card */}
          <div className="bg-gradient-to-br from-surface-container-lowest via-surface-container-lowest to-surface-container-low rounded-3xl border border-outline-variant/40 p-6 md:p-8 shadow-sm">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
              {/* Left: Department & Now Serving */}
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-black uppercase tracking-wider text-primary bg-primary/10 px-3 py-1 rounded-full">
                    {selectedDepartment.toUpperCase()}
                  </span>
                  <span className="text-xs text-on-surface-variant font-medium">
                    {departmentQueue?.hospital_name || 'Clinova General Hospital'}
                  </span>
                </div>

                <div className="flex items-baseline gap-4">
                  <div>
                    <span className="text-xs font-bold uppercase tracking-wider text-on-surface-variant block">
                      Now Serving
                    </span>
                    <div className="flex items-baseline gap-2 mt-1">
                      <span className="text-5xl md:text-6xl font-black text-primary font-mono tracking-tight">
                        {departmentQueue?.now_serving ? `Token ${departmentQueue.now_serving}` : 'None'}
                      </span>
                      {servingEntry && (
                        <span className="text-sm font-semibold text-on-surface-variant bg-surface-container px-2.5 py-1 rounded-lg">
                          {servingEntry.patient_display_name}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Waiting Token Number Sequence */}
                <div className="pt-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-on-surface-variant block mb-2">
                    Waiting Tokens ({waitingEntries.length})
                  </span>
                  {waitingEntries.length === 0 ? (
                    <span className="text-xs text-on-surface-variant italic">No patients currently waiting</span>
                  ) : (
                    <div className="flex flex-wrap items-center gap-2">
                      {waitingEntries.map((entry) => (
                        <span
                          key={entry.consultation_id}
                          className="px-3.5 py-1.5 rounded-xl bg-surface-container-high border border-outline-variant/40 text-on-surface font-mono font-bold text-sm shadow-xs flex items-center gap-1.5"
                          title={`${entry.patient_display_name} (Position #${entry.position})`}
                        >
                          <span className="text-primary">#</span>
                          <span>{entry.token_number}</span>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Right: Call Next Patient Action */}
              <div className="flex flex-col items-start lg:items-end justify-center gap-3 pt-4 lg:pt-0 lg:border-l lg:border-outline-variant/20 lg:pl-8">
                <button
                  type="button"
                  onClick={handleAdvanceQueue}
                  disabled={advancing || waitingEntries.length === 0}
                  className="w-full lg:w-auto px-8 py-4 rounded-2xl bg-primary hover:bg-primary-container text-on-primary font-black text-sm shadow-lg shadow-primary/20 transition-all flex items-center justify-center gap-3 disabled:opacity-40 disabled:cursor-not-allowed hover:scale-[1.02] active:scale-[0.98]"
                >
                  {advancing ? (
                    <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <>
                      <span className="material-symbols-outlined text-[24px]">campaign</span>
                      <span>Call Next Patient</span>
                    </>
                  )}
                </button>
                <p className="text-[11px] text-on-surface-variant text-center lg:text-right max-w-xs">
                  Advances the queue for {selectedDepartment}. Patient mobile status automatically updates to "In Consultation".
                </p>
              </div>
            </div>
          </div>

          {/* Department Queue Entries Table */}
          <div className="bg-surface-container-lowest rounded-2xl border border-outline-variant/30 shadow-xs overflow-hidden">
            <div className="p-4 border-b border-outline-variant/20 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-[20px]">format_list_numbered</span>
                <h3 className="font-bold text-sm text-on-surface">
                  {selectedDepartment} Queue Roster
                </h3>
              </div>
              {isReceptionist && (
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider bg-slate-100 px-2 py-0.5 rounded-full">
                  Non-Clinical Operational View
                </span>
              )}
            </div>

            {loading ? (
              <div className="p-12">
                <LoadingSpinner text="Loading department queue..." />
              </div>
            ) : !departmentQueue || departmentQueue.entries.length === 0 ? (
              <div className="p-12 text-center text-on-surface-variant">
                <span className="material-symbols-outlined text-4xl text-slate-300 block mb-2">inbox</span>
                <p className="text-xs font-semibold">No patients currently registered in {selectedDepartment}</p>
                <p className="text-[11px] text-slate-400 mt-1">
                  New registrations from the reception desk will immediately appear here.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-on-surface text-xs min-w-[650px]">
                  <thead className="bg-surface-container-low text-on-surface-variant font-bold border-b border-outline-variant/20">
                    <tr>
                      <th className="py-3 px-4 uppercase tracking-wider">Token</th>
                      <th className="py-3 px-4 uppercase tracking-wider">Patient</th>
                      <th className="py-3 px-4 uppercase tracking-wider">Department</th>
                      <th className="py-3 px-4 uppercase tracking-wider">Queue Position</th>
                      <th className="py-3 px-4 uppercase tracking-wider">Status</th>
                      <th className="py-3 px-4 uppercase tracking-wider">Check-in Time</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-outline-variant/10 font-medium">
                    {departmentQueue.entries.map((entry) => {
                      const isServing = entry.status === 'in_progress';
                      return (
                        <tr
                          key={entry.consultation_id}
                          className={`transition-colors ${
                            isServing ? 'bg-primary/5 font-semibold' : 'hover:bg-surface-container-low/50'
                          }`}
                        >
                          <td className="py-3.5 px-4">
                            <span
                              className={`inline-flex items-center justify-center font-mono font-black text-sm px-3 py-1 rounded-xl ${
                                isServing
                                  ? 'bg-primary text-on-primary shadow-xs'
                                  : 'bg-surface-container text-on-surface'
                              }`}
                            >
                              #{entry.token_number}
                            </span>
                          </td>
                          <td className="py-3.5 px-4">
                            <div className="flex flex-col">
                              <span className="font-bold text-on-surface">
                                {entry.patient_display_name}
                              </span>
                              <span className="text-[10px] text-on-surface-variant font-mono">
                                #{entry.consultation_id.slice(0, 8)}
                              </span>
                            </div>
                          </td>
                          <td className="py-3.5 px-4 font-semibold text-on-surface-variant">
                            {entry.department}
                          </td>
                          <td className="py-3.5 px-4">
                            {isServing ? (
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-primary/10 text-primary">
                                Current
                              </span>
                            ) : (
                              <span className="text-on-surface-variant font-semibold">
                                #{entry.position} in line
                              </span>
                            )}
                          </td>
                          <td className="py-3.5 px-4">
                            {isServing ? (
                              <span className="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-100 text-emerald-800 flex items-center gap-1 w-fit">
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse" />
                                Now Serving
                              </span>
                            ) : (
                              <span className="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-amber-50 text-amber-800 border border-amber-200 flex items-center gap-1 w-fit">
                                Waiting
                              </span>
                            )}
                          </td>
                          <td className="py-3.5 px-4 text-on-surface-variant">
                            {new Date(entry.checkin_time).toLocaleTimeString([], {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ALL HOSPITAL CASES VIEW */}
      {viewMode === 'all' && (
        <div className="space-y-4">
          <QueueMetrics
            total={consultations.length}
            waiting={consultations.filter((c) => c.status === 'initiated').length}
            inProgress={consultations.filter((c) => c.status === 'in_progress').length}
            completed={consultations.filter((c) => c.status === 'completed' || c.status === 'reviewed').length}
          />

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

            {loading ? (
              <LoadingSpinner text="Refreshing OPD consultation queue..." />
            ) : (
              <QueueTable
                consultations={consultations.filter((c) => {
                  if (!searchQuery.trim()) return true;
                  const q = searchQuery.toLowerCase();
                  const idMatch = c.patient_id.toLowerCase().includes(q) || c.id.toLowerCase().includes(q);
                  const complaintMatch = c.chief_complaint ? c.chief_complaint.toLowerCase().includes(q) : false;
                  return idMatch || complaintMatch;
                })}
                onSelectConsultation={(c: Consultation) => navigate(`/consultation/${c.id}`)}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
};
