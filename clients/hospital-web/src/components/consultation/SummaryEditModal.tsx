import React, { useState, useEffect } from 'react';
import { Modal } from '../common/Modal';
import { SummaryResponse } from '../../types/summary';

interface SummaryEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  summary: SummaryResponse | null;
  onSave: (summaryText: string, clinicianNotes: string) => Promise<void>;
  isSaving: boolean;
}

export const SummaryEditModal: React.FC<SummaryEditModalProps> = ({
  isOpen,
  onClose,
  summary,
  onSave,
  isSaving,
}) => {
  const [text, setText] = useState('');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (summary) {
      setText(summary.summary_text || '');
      setNotes(summary.clinician_notes || '');
      setError(null);
    }
  }, [summary, isOpen]);

  const handleSave = async () => {
    if (!text.trim()) {
      setError('Summary text cannot be blank.');
      return;
    }
    setError(null);
    try {
      await onSave(text, notes);
      onClose();
    } catch (err: any) {
      if (err.response?.status === 409) {
        setError('Summary was updated by another user or session. Please refresh before saving.');
      } else {
        setError(err.response?.data?.detail || 'Failed to save summary draft.');
      }
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Edit Clinical Summary Draft" maxWidth="max-w-2xl">
      <div className="flex flex-col gap-4">
        <div className="bg-amber-50 border border-amber-200/80 rounded-xl p-3 flex items-start gap-2.5">
          <span className="material-symbols-outlined text-amber-700 text-[18px] shrink-0 mt-0.5">edit_note</span>
          <p className="text-xs text-amber-900 leading-snug">
            You are editing the draft as an attending clinician. Changes are recorded under your clinical session and version-controlled.
          </p>
        </div>

        {error && (
          <div className="bg-error-container/40 border border-error-container p-3 rounded-xl text-xs text-error font-medium">
            {error}
          </div>
        )}

        {/* Narrative Summary Editor */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-bold text-slate-700" htmlFor="edit-summary-text">
            Summary Narrative
          </label>
          <textarea
            id="edit-summary-text"
            rows={6}
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={isSaving}
            className="w-full p-3 rounded-xl border border-slate-300 text-sm font-medium focus:border-primary focus:ring-1 focus:ring-primary leading-relaxed resize-y"
            placeholder="Edit summary narrative..."
          />
        </div>

        {/* Clinician Notes Editor */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-bold text-slate-700" htmlFor="edit-clinician-notes">
            Clinician Commentary / Internal Notes
          </label>
          <textarea
            id="edit-clinician-notes"
            rows={3}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            disabled={isSaving}
            className="w-full p-3 rounded-xl border border-slate-300 text-sm font-medium focus:border-primary focus:ring-1 focus:ring-primary leading-relaxed resize-y"
            placeholder="Add internal clinician remarks (e.g. verified with patient directly, ordered CBC follow-up)..."
          />
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
          <button
            type="button"
            onClick={onClose}
            disabled={isSaving}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={isSaving}
            className="px-5 py-2 rounded-xl bg-primary hover:bg-primary-container text-on-primary text-xs font-bold transition-colors flex items-center gap-1.5 shadow-xs"
          >
            {isSaving ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Saving Draft...</span>
              </>
            ) : (
              <>
                <span className="material-symbols-outlined text-[16px]">save</span>
                <span>Save Changes</span>
              </>
            )}
          </button>
        </div>
      </div>
    </Modal>
  );
};
