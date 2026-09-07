import React from 'react';

interface LoadingSpinnerProps {
  label?: string;
  text?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  label,
  text,
  size = 'md',
}) => {
  const displayText = text || label || 'Loading clinical data...';
  const sizeClasses = {
    sm: 'w-5 h-5 border-2',
    md: 'w-8 h-8 border-3',
    lg: 'w-12 h-12 border-4',
  }[size];

  return (
    <div className="flex flex-col items-center justify-center p-8 gap-3">
      <div
        className={`${sizeClasses} border-primary/20 border-t-primary rounded-full animate-spin`}
      />
      {displayText && <span className="text-xs font-medium text-on-surface-variant">{displayText}</span>}
    </div>
  );
};
