import React, { useState } from 'react';
import { Modal } from '../common/Modal';

interface SummaryRejectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onReject: (reason: string) => Promise<void>;
  isRejecting: boolean;
}

export const SummaryRejectModal: React.FC<SummaryRejectModalProps> = ({
  isOpen,
  onClose,
  onReject,
  isRejecting,
}) => {
  const [reason, setReason] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleReject = async () => {
    if (reason.trim().length < 3) {
      setError('Please provide a clinical reason (at least 3 characters).');
      return;
    }
    setError(null);
    try {
      await onReject(reason.trim());
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reject summary draft.');
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Reject Clinical Summary Draft">
      <div className="flex flex-col gap-4">
        <div className="bg-error-container/30 border border-error/30 rounded-xl p-3 flex items-start gap-2.5">
          <span className="material-symbols-outlined text-error text-[20px] shrink-0 mt-0.5">
            rule
          </span>
          <div className="flex flex-col text-xs text-on-surface leading-snug">
            <span className="font-bold text-error">Clinical Rejection Protocol</span>
            <span>
              Rejecting this draft flags the summary as clinically unsuitable or inaccurate. A valid clinical rationale is required by NABH compliance standards.
            </span>
          </div>
        </div>

        {error && (
          <div className="bg-error-container/40 border border-error-container p-3 rounded-xl text-xs text-error font-medium">
            {error}
          </div>
        )}

        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-bold text-slate-700" htmlFor="reject-reason">
            Clinical Reason for Rejection <span className="text-error">*</span>
          </label>
          <textarea
            id="reject-reason"
            rows={3}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            disabled={isRejecting}
            className="w-full p-3 rounded-xl border border-slate-300 text-sm font-medium focus:border-error focus:ring-1 focus:ring-error leading-relaxed resize-y"
            placeholder="e.g. Patient reports contradictory symptom timeline; OCR missed prior surgical contraindications."
          />
        </div>

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
          <button
            type="button"
            onClick={onClose}
            disabled={isRejecting}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleReject}
            disabled={isRejecting}
            className="px-5 py-2 rounded-xl bg-error hover:bg-red-700 text-on-error text-xs font-bold transition-colors flex items-center gap-1.5 shadow-xs"
          >
            {isRejecting ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Rejecting...</span>
              </>
            ) : (
              <>
                <span className="material-symbols-outlined text-[16px]">cancel</span>
                <span>Reject Draft</span>
              </>
            )}
          </button>
        </div>
      </div>
    </Modal>
  );
};
