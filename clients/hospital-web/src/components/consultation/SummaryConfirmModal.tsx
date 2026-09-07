import React, { useState } from 'react';
import { Modal } from '../common/Modal';

interface SummaryConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (notes?: string) => Promise<void>;
  isConfirming: boolean;
}

export const SummaryConfirmModal: React.FC<SummaryConfirmModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  isConfirming,
}) => {
  const [finalNotes, setFinalNotes] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleConfirm = async () => {
    setError(null);
    try {
      await onConfirm(finalNotes.trim() ? finalNotes : undefined);
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to confirm and finalize summary.');
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Confirm & Finalize Clinical Summary">
      <div className="flex flex-col gap-4">
        <div className="bg-teal-50 border border-teal-200 rounded-xl p-3 flex items-start gap-2.5">
          <span className="material-symbols-outlined text-teal-700 text-[20px] shrink-0 mt-0.5">
            verified
          </span>
          <div className="flex flex-col text-xs text-teal-950 leading-snug">
            <span className="font-bold">Physician Finalization Sign-Off</span>
            <span>
              By confirming, you certify that you have reviewed the clinical findings, timeline, and intake summary. The summary will be marked <strong>CONFIRMED</strong> and the consultation status advanced.
            </span>
          </div>
        </div>

        {error && (
          <div className="bg-error-container/40 border border-error-container p-3 rounded-xl text-xs text-error font-medium">
            {error}
          </div>
        )}

        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-bold text-slate-700" htmlFor="confirm-notes">
            Final Sign-off Notes (Optional)
          </label>
          <textarea
            id="confirm-notes"
            rows={3}
            value={finalNotes}
            onChange={(e) => setFinalNotes(e.target.value)}
            disabled={isConfirming}
            className="w-full p-3 rounded-xl border border-slate-300 text-sm font-medium focus:border-primary focus:ring-1 focus:ring-primary leading-relaxed resize-y"
            placeholder="e.g. Case reviewed with patient present. Vitals stable. Prescription issued."
          />
        </div>

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
          <button
            type="button"
            onClick={onClose}
            disabled={isConfirming}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={isConfirming}
            className="px-5 py-2 rounded-xl bg-primary hover:bg-primary-container text-on-primary text-xs font-bold transition-colors flex items-center gap-1.5 shadow-xs"
          >
            {isConfirming ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Confirming...</span>
              </>
            ) : (
              <>
                <span className="material-symbols-outlined text-[16px]">check_circle</span>
                <span>Confirm & Sign-Off</span>
              </>
            )}
          </button>
        </div>
      </div>
    </Modal>
  );
};
