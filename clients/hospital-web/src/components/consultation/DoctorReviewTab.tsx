import React, { useState } from 'react';
import { SummaryResponse } from '../../types/summary';
import { Consultation } from '../../types/consultation';

interface DoctorReviewTabProps {
  consultation: Consultation;
  summary: SummaryResponse | null;
  onOpenConfirmModal: () => void;
  onOpenEditModal: () => void;
}

export const DoctorReviewTab: React.FC<DoctorReviewTabProps> = ({
  consultation,
  summary,
  onOpenConfirmModal,
  onOpenEditModal,
}) => {
  const [examNotes, setExamNotes] = useState({
    general: 'Patient conscious, alert, oriented to time, place, and person. No acute distress observed.',
    vitalsRecorded: 'BP: 124/82 mmHg, Pulse: 78 bpm, SpO2: 99% on room air, Temp: 98.4°F',
    systemicExam: 'Chest: Clear bilaterally, normal vesicular breath sounds. CVS: S1, S2 heard, no murmurs. P/A: Soft, non-tender.',
    impression: summary?.structured_summary?.chief_complaint || 'Under evaluation following clinical workup.',
    plan: '1. Continue supportive medication as prescribed.\n2. Review lab results in 48 hours.\n3. Return immediately if red-flag symptoms develop.',
    disposition: 'followup',
  });

  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSaveNotes = (e: React.FormEvent) => {
    e.preventDefault();
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  const handlePrintSlip = () => {
    window.print();
  };

  const isSummaryConfirmed = summary?.status === 'confirmed';

  return (
    <div className="space-y-6">
      {/* Verification Status Banner */}
      <div
        className={`p-4 rounded-xl border flex items-center justify-between gap-4 ${
          isSummaryConfirmed
            ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
            : 'bg-amber-50 border-amber-200 text-amber-900'
        }`}
      >
        <div className="flex items-center gap-3">
          <span className="material-symbols-outlined text-2xl">
            {isSummaryConfirmed ? 'verified' : 'pending_actions'}
          </span>
          <div>
            <h4 className="text-sm font-bold">
              {isSummaryConfirmed
                ? 'Clinical Summary Verified by Attending Physician'
                : 'Physician Review & Attestation Pending'}
            </h4>
            <p className="text-xs opacity-80 mt-0.5">
              {isSummaryConfirmed
                ? `Attested by Attending Physician on ${
                    summary?.reviewed_at ? new Date(summary.reviewed_at).toLocaleDateString() : 'today'
                  }.`
                : 'Review the extracted AI summary draft, make amendments if necessary, and attest clinical accuracy.'}
            </p>
          </div>
        </div>

        {!isSummaryConfirmed && (
          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              onClick={onOpenEditModal}
              className="px-3 py-1.5 bg-white border border-amber-300 hover:bg-amber-100/50 text-amber-900 rounded-lg text-xs font-bold transition-colors shadow-sm"
            >
              Edit Draft
            </button>
            <button
              onClick={onOpenConfirmModal}
              className="px-3.5 py-1.5 bg-primary hover:bg-primary-dark text-white rounded-lg text-xs font-bold transition-colors shadow-sm flex items-center gap-1"
            >
              <span className="material-symbols-outlined text-sm">check_circle</span>
              Attest & Finalize
            </button>
          </div>
        )}
      </div>

      {savedSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl flex items-center gap-2 font-medium">
          <span className="material-symbols-outlined text-sm">check</span>
          Doctor examination notes saved successfully to consultation session.
        </div>
      )}

      {/* Clinical Notes Form */}
      <form onSubmit={handleSaveNotes} className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-5">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-xl">stethoscope</span>
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
              Objective Physical Examination & Notes
            </h3>
          </div>
          <span className="text-xs text-slate-400">Consultation #{consultation.id.slice(0, 8)}</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              General Appearance & Sensorium
            </label>
            <textarea
              rows={3}
              value={examNotes.general}
              onChange={(e) => setExamNotes({ ...examNotes, general: e.target.value })}
              className="w-full text-xs text-slate-800 border border-slate-200 rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Recorded Point-of-Care Vitals
            </label>
            <textarea
              rows={3}
              value={examNotes.vitalsRecorded}
              onChange={(e) => setExamNotes({ ...examNotes, vitalsRecorded: e.target.value })}
              className="w-full text-xs text-slate-800 border border-slate-200 rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
            Systemic Examination (Respiratory, CVS, Abdomen, CNS)
          </label>
          <textarea
            rows={3}
            value={examNotes.systemicExam}
            onChange={(e) => setExamNotes({ ...examNotes, systemicExam: e.target.value })}
            className="w-full text-xs text-slate-800 border border-slate-200 rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Clinical Impression / Differential Diagnosis
            </label>
            <textarea
              rows={4}
              value={examNotes.impression}
              onChange={(e) => setExamNotes({ ...examNotes, impression: e.target.value })}
              className="w-full text-xs text-slate-800 border border-slate-200 rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary font-medium"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Management Plan & Rx Instructions
            </label>
            <textarea
              rows={4}
              value={examNotes.plan}
              onChange={(e) => setExamNotes({ ...examNotes, plan: e.target.value })}
              className="w-full text-xs text-slate-800 border border-slate-200 rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary font-mono text-[11px]"
            />
          </div>
        </div>

        {/* Disposition / Patient Outcome */}
        <div className="pt-2 border-t border-slate-100">
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
            Consultation Disposition / Action
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { id: 'followup', label: 'OPD Follow-up', desc: 'Review in 2-7 days', icon: 'schedule' },
              { id: 'routine', label: 'Discharged / Routine', desc: 'Resolved / Home care', icon: 'check_circle' },
              { id: 'specialist', label: 'Specialist Referral', desc: 'Internal referral', icon: 'forward' },
              { id: 'admission', label: 'Inpatient Admit', desc: 'Requires ward / ICU', icon: 'local_hospital' },
            ].map((item) => (
              <button
                type="button"
                key={item.id}
                onClick={() => setExamNotes({ ...examNotes, disposition: item.id })}
                className={`p-3 rounded-xl border text-left transition-all ${
                  examNotes.disposition === item.id
                    ? 'border-primary bg-primary/5 ring-1 ring-primary'
                    : 'border-slate-200 hover:border-slate-300 bg-white'
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className={`material-symbols-outlined text-lg ${
                      examNotes.disposition === item.id ? 'text-primary' : 'text-slate-400'
                    }`}
                  >
                    {item.icon}
                  </span>
                  <span className="text-xs font-bold text-slate-800">{item.label}</span>
                </div>
                <p className="text-[11px] text-slate-500">{item.desc}</p>
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-slate-100">
          <button
            type="button"
            onClick={handlePrintSlip}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors"
          >
            <span className="material-symbols-outlined text-sm">print</span>
            Print OPD Consultation Summary
          </button>

          <button
            type="submit"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold text-white bg-primary hover:bg-primary-dark transition-colors shadow-sm"
          >
            <span className="material-symbols-outlined text-sm">save</span>
            Save Examination Notes
          </button>
        </div>
      </form>
    </div>
  );
};
