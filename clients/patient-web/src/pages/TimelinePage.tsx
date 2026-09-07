import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePatient } from '../context/PatientContext';
import { timelineApi } from '../api';
import { TimelineEvent, TimelineEventType } from '../types';
import ProgressSteps from '../components/ProgressSteps';
import { 
  Clock, 
  Calendar, 
  RefreshCw, 
  ArrowRight, 
  FileText, 
  Activity, 
  AlertCircle, 
  Pill, 
  Stethoscope, 
  ShieldCheck, 
  Filter,
  CheckCircle2,
  ChevronRight
} from 'lucide-react';

const FILTER_TABS: { key: string; label: string; icon: string }[] = [
  { key: 'ALL', label: 'All Events', icon: 'view_timeline' },
  { key: 'CONSULTATION', label: 'Consultations', icon: 'stethoscope' },
  { key: 'DIAGNOSIS', label: 'Diagnoses', icon: 'medical_services' },
  { key: 'MEDICATION', label: 'Medications', icon: 'prescriptions' },
  { key: 'INVESTIGATION', label: 'Lab Tests', icon: 'biotech' },
];

export const TimelinePage: React.FC = () => {
  const navigate = useNavigate();
  const { currentPatient, currentConsultation } = usePatient();

  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [rebuilding, setRebuilding] = useState(false);
  const [filter, setFilter] = useState<string>('ALL');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!currentPatient) {
      navigate('/identify');
      return;
    }
    loadTimeline();
  }, [currentPatient]);

  const loadTimeline = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await timelineApi.getMyTimeline();
      setEvents(res.events || []);
    } catch (err: any) {
      console.error('Failed to load timeline:', err);
      setError(err.response?.data?.detail || 'Failed to fetch medical timeline');
    } finally {
      setLoading(false);
    }
  };

  const handleRebuildTimeline = async () => {
    setRebuilding(true);
    setError(null);
    try {
      const res = await timelineApi.rebuildTimeline();
      setEvents(res.events || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to rebuild timeline');
    } finally {
      setRebuilding(false);
    }
  };

  const filteredEvents = events.filter(e => {
    if (filter === 'ALL') return true;
    return e.event_type.toUpperCase() === filter;
  });

  const getEventIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'consultation':
        return <Stethoscope className="w-4 h-4 text-primary" />;
      case 'medication':
        return <Pill className="w-4 h-4 text-secondary" />;
      case 'diagnosis':
        return <Activity className="w-4 h-4 text-rose-600" />;
      case 'investigation':
        return <FileText className="w-4 h-4 text-blue-600" />;
      default:
        return <Calendar className="w-4 h-4 text-on-surface-variant" />;
    }
  };

  return (
    <div className="min-h-screen bg-surface flex flex-col items-center">
      {/* Top Header */}
      <header className="sticky top-0 z-30 w-full bg-surface-container-lowest/90 backdrop-blur-xl border-b border-surface-container-low shadow-sm px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button 
            onClick={() => navigate('/upload')}
            className="w-10 h-10 rounded-full flex items-center justify-center text-on-surface-variant hover:bg-surface-container-low transition active:scale-95"
          >
            <span className="material-symbols-outlined text-[24px]">arrow_back</span>
          </button>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary text-on-primary flex items-center justify-center font-bold text-sm">
              C
            </div>
            <div className="flex flex-col">
              <span className="font-headline-sm text-sm font-bold text-primary tracking-tight leading-none">CLINOVA</span>
              <span className="font-caption text-[11px] text-on-surface-variant font-medium">Chronological Health Timeline</span>
            </div>
          </div>
        </div>

        <button 
          onClick={handleRebuildTimeline}
          disabled={rebuilding}
          className="text-xs font-bold text-primary hover:text-primary-container px-3 py-1.5 rounded-lg border border-outline-variant hover:bg-surface-container-low transition flex items-center gap-1.5"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${rebuilding ? 'animate-spin' : ''}`} />
          <span>Sync Timeline</span>
        </button>
      </header>

      {/* Main Container */}
      <main className="w-full max-w-xl px-4 py-4 flex flex-col gap-5 pb-24">
        {/* Stepper Header */}
        <ProgressSteps 
          currentStep={6} 
          stepTitle="Structured Medical Timeline" 
          totalSteps={7} 
        />

        {/* Introduction Banner */}
        <div className="bg-surface-container-low rounded-2xl p-4 border border-outline-variant/30 flex flex-col gap-1.5">
          <div className="flex items-center gap-1.5 text-primary text-xs font-bold uppercase tracking-wider">
            <span className="material-symbols-outlined text-[18px]">history_edu</span>
            Unified Longitudinal Record
          </div>
          <h1 className="font-headline-sm text-xl font-bold text-on-surface">
            Your Medical History Timeline
          </h1>
          <p className="font-body-md text-xs text-on-surface-variant">
            Clinova automatically synthesizes events from your previous visits, prescriptions, and AI intake into a clean chronological timeline for your doctor.
          </p>
        </div>

        {/* Filter Chips */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
          {FILTER_TABS.map(tab => (
            <button
              key={tab.key}
              type="button"
              onClick={() => setFilter(tab.key)}
              className={`shrink-0 min-h-[36px] px-3.5 rounded-full flex items-center gap-1.5 text-xs font-bold transition-all ${
                filter === tab.key
                  ? 'bg-primary text-on-primary shadow-sm'
                  : 'bg-surface-container-lowest text-on-surface-variant border border-outline-variant/30 hover:bg-surface-container-low'
              }`}
            >
              <span className="material-symbols-outlined text-[16px]">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Error State */}
        {error && (
          <div className="p-3 bg-error-container text-on-error-container rounded-xl flex items-start gap-2.5 text-xs font-semibold">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Loading Spinner */}
        {loading ? (
          <div className="p-8 text-center flex flex-col items-center gap-3">
            <RefreshCw className="w-6 h-6 text-primary animate-spin" />
            <p className="font-label-lg text-xs font-bold text-on-surface">Assembling clinical timeline...</p>
          </div>
        ) : filteredEvents.length === 0 ? (
          /* Empty Timeline State */
          <div className="p-8 rounded-2xl bg-surface-container-lowest border border-dashed border-outline-variant/50 text-center flex flex-col items-center gap-2.5">
            <Clock className="w-10 h-10 text-on-surface-variant/40" />
            <h3 className="font-label-lg text-sm font-bold text-on-surface">No events recorded in this category</h3>
            <p className="font-caption text-xs text-on-surface-variant max-w-xs">
              Medical events from your consultation, AI interview responses, and uploaded documents appear here automatically.
            </p>
            <button
              type="button"
              onClick={handleRebuildTimeline}
              disabled={rebuilding}
              className="mt-2 px-4 py-2 rounded-xl bg-secondary-container text-on-secondary-container text-xs font-bold flex items-center gap-1.5"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${rebuilding ? 'animate-spin' : ''}`} />
              Re-scan Encounters
            </button>
          </div>
        ) : (
          /* Chronological Event Cards */
          <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-outline-variant/40">
            {filteredEvents.map((event, idx) => (
              <div 
                key={event.id || idx}
                className="relative bg-surface-container-lowest p-4 rounded-2xl border border-outline-variant/40 shadow-xs flex flex-col gap-2 hover:border-primary/40 transition-colors"
              >
                {/* Timeline node dot */}
                <div className="absolute -left-6 top-5 w-3 h-3 rounded-full bg-primary ring-4 ring-surface" />

                {/* Event Header */}
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <div className="w-7 h-7 rounded-lg bg-surface-container-low flex items-center justify-center shrink-0">
                      {getEventIcon(event.event_type)}
                    </div>
                    <div className="flex flex-col min-w-0">
                      <span className="font-caption text-[10px] text-primary font-bold uppercase tracking-wider">
                        {event.event_type}
                      </span>
                      <h3 className="font-label-lg text-sm font-bold text-on-surface truncate">
                        {event.title}
                      </h3>
                    </div>
                  </div>

                  {/* Date Precision Chip */}
                  <span className="px-2 py-0.5 rounded-full bg-surface-container-low text-on-surface-variant text-[10px] font-bold shrink-0">
                    {event.date_precision || 'EXACT'}
                  </span>
                </div>

                {/* Event Description */}
                {event.description && (
                  <p className="font-body-md text-xs text-on-surface-variant leading-relaxed">
                    {event.description}
                  </p>
                )}

                {/* Footer Badges */}
                <div className="pt-2 border-t border-surface-container flex items-center justify-between text-[11px]">
                  <div className="flex items-center gap-1 text-on-surface-variant">
                    <Calendar className="w-3.5 h-3.5" />
                    <span>{new Date(event.event_date).toLocaleDateString('en-IN', {
                      day: 'numeric',
                      month: 'short',
                      year: 'numeric'
                    })}</span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <span className="px-2 py-0.5 rounded bg-surface-container-high text-on-surface-variant text-[10px] font-medium">
                      Source: {event.source_type}
                    </span>
                    {event.is_verified && (
                      <span className="px-1.5 py-0.5 rounded bg-secondary-container text-on-secondary-container text-[10px] font-bold flex items-center gap-0.5">
                        <CheckCircle2 className="w-3 h-3" />
                        Verified
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Action Controls */}
        <div className="pt-3 space-y-2.5">
          <button
            type="button"
            onClick={() => navigate('/summary')}
            className="w-full h-12 rounded-xl bg-primary text-on-primary font-bold text-sm flex items-center justify-center gap-2 shadow-md hover:bg-primary-container active:scale-[0.99] transition-all"
          >
            <span>Continue to Review & Submit</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <button
            type="button"
            onClick={() => navigate('/upload')}
            className="w-full h-10 rounded-xl bg-surface-container-lowest text-on-surface-variant border border-outline-variant/40 font-semibold text-xs flex items-center justify-center gap-1 hover:bg-surface-container-low transition"
          >
            Back to Document Upload
          </button>
        </div>
      </main>
    </div>
  );
};
export default TimelinePage;
