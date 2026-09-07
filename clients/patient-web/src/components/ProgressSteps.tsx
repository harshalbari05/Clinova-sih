import React from 'react';
import { Check } from 'lucide-react';

export interface StepItem {
  id: string;
  label: string;
  path: string;
}

export const INTAKE_STEPS: StepItem[] = [
  { id: 'identify', label: 'Identify', path: '/identify' },
  { id: 'consent', label: 'Consent', path: '/consent' },
  { id: 'language', label: 'Language', path: '/language' },
  { id: 'interview', label: 'Interview', path: '/interview' },
  { id: 'upload', label: 'Documents', path: '/upload' },
  { id: 'timeline', label: 'Timeline', path: '/timeline' },
  { id: 'summary', label: 'Summary', path: '/summary' },
];

export interface ProgressStepsProps {
  currentStepIndex?: number; // 0 to 6
  currentStep?: number; // 1 to 7
  stepTitle?: string;
  totalSteps?: number;
}

export const ProgressSteps: React.FC<ProgressStepsProps> = ({ 
  currentStepIndex, 
  currentStep, 
  stepTitle,
  totalSteps = 7 
}) => {
  const stepIdx = typeof currentStepIndex === 'number' 
    ? currentStepIndex 
    : (typeof currentStep === 'number' ? currentStep - 1 : 0);
  const progressPercent = Math.round(((stepIdx + 1) / totalSteps) * 100);
  const currentTitle = stepTitle || INTAKE_STEPS[stepIdx]?.label || '';

  return (
    <div className="w-full bg-surface-container-lowest p-4 rounded-2xl shadow-sm border border-outline-variant/30 mb-6">
      {/* Step Header */}
      <div className="flex items-center justify-between mb-2.5">
        <div className="flex items-baseline gap-2">
          <span className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">Step</span>
          <span className="text-lg font-bold text-primary">{stepIdx + 1}</span>
          <span className="text-xs font-semibold text-on-surface-variant">of {totalSteps}</span>
          <span className="text-outline-variant">•</span>
          <span className="text-sm font-bold text-on-surface">
            {currentTitle}
          </span>
        </div>
        <span className="text-xs font-bold text-primary">{progressPercent}% Completed</span>
      </div>

      {/* Linear Progress Bar */}
      <div className="w-full bg-surface-container h-2 rounded-full overflow-hidden mb-3">
        <div
          className="bg-primary h-full transition-all duration-300 ease-out rounded-full"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Step Pills Row */}
      <div className="flex items-center justify-between gap-1 overflow-x-auto pb-1">
        {INTAKE_STEPS.map((step, idx) => {
          const isPassed = idx < stepIdx;
          const isCurrent = idx === stepIdx;

          return (
            <div
              key={step.id}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
                isCurrent
                  ? 'bg-primary text-on-primary shadow-xs'
                  : isPassed
                  ? 'bg-secondary-container/60 text-on-secondary-container'
                  : 'bg-surface-container-low text-on-surface-variant'
              }`}
            >
              {isPassed ? (
                <Check className="w-3 h-3 text-secondary" strokeWidth={3} />
              ) : (
                <span className="w-3.5 text-center">{idx + 1}</span>
              )}
              <span className="hidden sm:inline">{step.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ProgressSteps;
