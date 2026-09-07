import React from 'react';

interface ErrorAlertProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({
  title = 'An error occurred',
  message,
  onRetry,
  onDismiss,
}) => {
  return (
    <div className="rounded-xl bg-error-container/30 border border-error-container p-4 flex items-start justify-between gap-4">
      <div className="flex items-start gap-3">
        <span className="material-symbols-outlined text-error text-[22px] shrink-0 mt-0.5">
          error
        </span>
        <div className="flex flex-col">
          <span className="text-sm font-bold text-on-surface">{title}</span>
          <p className="text-xs text-on-surface-variant mt-0.5">{message}</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-3 py-1.5 rounded-lg bg-surface-container-lowest hover:bg-surface-container text-xs font-semibold text-primary transition-colors shrink-0"
            type="button"
          >
            Retry
          </button>
        )}
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="p-1 rounded-lg hover:bg-surface-container text-on-surface-variant transition-colors"
            type="button"
          >
            <span className="material-symbols-outlined text-base">close</span>
          </button>
        )}
      </div>
    </div>
  );
};
