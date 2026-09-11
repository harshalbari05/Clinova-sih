import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Consultation } from '../types/consultation';
import { listConsultations } from '../api/consultations';
import { QueueMetrics } from '../components/queue/QueueMetrics';
import { QueueTable } from '../components/queue/QueueTable';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';

export const DashboardPage: React.FC = () => {
  const { user, hospital, hospitalRole } = useAuth();
  const isReceptionist = hospitalRole === 'receptionist';
  const navigate = useNavigate();

  const [consultations, setConsultations] = useState<Consultation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchQueue = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await listConsultations({ limit: 50 });
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
  }, []);

  const waitingCount = consultations.filter((c) => c.status === 'initiated').length;
  const inProgressCount = consultations.filter((c) => c.status === 'in_progress').length;
  const completedCount = consultations.filter((c) => c.status === 'completed' || c.status === 'reviewed').length;

  const nextPatient = consultations.find((c) => c.status === 'initiated' || c.status === 'in_progress');

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-primary to-primary-dark rounded-2xl p-6 text-white shadow-lg shadow-primary/20 relative overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-white/5 skew-x-12 pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase bg-white/20 text-white border border-white/25">
                {isReceptionist ? 'Reception Desk' : 'Active OPD Session'}
              </span>
              <span className="text-xs text-white/75">• {new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' })}</span>
            </div>
            <h1 className="text-2xl font-black tracking-tight">
              Welcome, {user?.full_name || (isReceptionist ? 'Reception Desk' : 'Dr. Amit Sharma')}
            </h1>
            <p className="text-xs text-teal-100 mt-1 max-w-xl">
              {hospital?.name || 'Department of General Medicine & OPD Triage'} — {isReceptionist ? 'Patient intake, QR verification & visit registration desk.' : 'Live patient intake with AI-assisted clinical summary & provenance verification.'}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/registration')}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-white text-primary text-xs font-bold shadow-md hover:bg-teal-50 transition-all"
            >
              <span className="material-symbols-outlined text-sm">how_to_reg</span>
              Register Patient
            </button>
            <button
              onClick={() => navigate('/queue')}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-semibold backdrop-blur-sm border border-white/15 transition-all"
            >
              <span className="material-symbols-outlined text-sm">view_list</span>
              OPD Queue
            </button>
          </div>
        </div>
      </div>

      {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

      {/* KPI Metrics */}
      <QueueMetrics
        total={consultations.length}
        waiting={waitingCount}
        inProgress={inProgressCount}
        completed={completedCount}
      />

      {/* Spotlight: Reception Action or Doctor Next Patient */}
      {isReceptionist ? (
        <div className="bg-white rounded-2xl border border-primary/30 p-5 shadow-sm hover:border-primary transition-all">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold">
                <span className="material-symbols-outlined text-[26px]">how_to_reg</span>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-primary uppercase tracking-wider">Fast Intake</span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-emerald-50 text-emerald-800 border border-emerald-200">
                    Desk Active
                  </span>
                </div>
                <h3 className="text-base font-bold text-slate-900 mt-0.5">
                  Register Arriving Outpatients
                </h3>
                <p className="text-xs text-slate-600 mt-0.5">
                  Scan Clinova patient QR or enter walk-in details to route patients to OPD departments.
                </p>
              </div>
            </div>

            <button
              onClick={() => navigate('/registration')}
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-dark text-white text-xs font-bold shadow-md shadow-primary/25 transition-all"
            >
              <span>Open Registration Desk</span>
              <span className="material-symbols-outlined text-sm">arrow_forward</span>
            </button>
          </div>
        </div>
      ) : nextPatient ? (
        <div className="bg-white rounded-2xl border border-teal-200 p-5 shadow-sm hover:border-primary transition-all">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-teal-50 border border-teal-200 flex flex-col items-center justify-center text-primary flex-shrink-0">
                <span className="text-[10px] font-bold uppercase tracking-wider text-teal-700">Token</span>
                <span className="text-lg font-black leading-tight">#1</span>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Next in Line</span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-amber-50 text-amber-800 border border-amber-200">
                    Ready for Consultation
                  </span>
                </div>
                <h3 className="text-base font-bold text-slate-900 mt-0.5">
                  Patient #{nextPatient.patient_id.slice(0, 8)}
                </h3>
                <p className="text-xs text-slate-600 mt-0.5">
                  <span className="font-semibold text-slate-700">Chief Complaint:</span>{' '}
                  {nextPatient.chief_complaint || 'General Clinical Consultation'}
                </p>
              </div>
            </div>

            <button
              onClick={() => navigate(`/consultation/${nextPatient.id}`)}
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-dark text-white text-xs font-bold shadow-md shadow-primary/25 transition-all"
            >
              <span>Call Patient & Open Case</span>
              <span className="material-symbols-outlined text-sm">arrow_forward</span>
            </button>
          </div>
        </div>
      ) : null}

      {/* Recent OPD Queue Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900">Today's OPD Queue</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Ordered in chronological queue sequence (FIFO) for systematic outpatient care.
            </p>
          </div>
          <button
            onClick={() => navigate('/queue')}
            className="text-xs font-bold text-primary hover:text-primary-dark flex items-center gap-1"
          >
            <span>View All Patients ({consultations.length})</span>
            <span className="material-symbols-outlined text-sm">chevron_right</span>
          </button>
        </div>

        {loading ? (
          <LoadingSpinner text="Fetching active OPD consultations..." />
        ) : (
          <QueueTable
            consultations={consultations.slice(0, 10)}
            onSelectConsultation={!isReceptionist ? (c: Consultation) => navigate(`/consultation/${c.id}`) : undefined}
          />
        )}
      </div>
    </div>
  );
};
