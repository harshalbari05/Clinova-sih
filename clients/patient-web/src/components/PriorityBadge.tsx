import React from 'react';
import { TriagePriority } from '../types';

interface PriorityBadgeProps {
  priority: TriagePriority | string;
  size?: 'sm' | 'md';
}

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({ priority, size = 'md' }) => {
  const p = priority.toLowerCase();

  const getStyle = () => {
    switch (p) {
      case 'red':
        return 'bg-error text-on-error border-error';
      case 'orange':
        return 'bg-amber-600 text-white border-amber-600';
      case 'yellow':
        return 'bg-amber-100 text-amber-900 border-amber-300';
      case 'green':
      default:
        return 'bg-secondary-container text-on-secondary-container border-secondary/30';
    }
  };

  const getLabel = () => {
    switch (p) {
      case 'red':
        return 'Emergency (Red)';
      case 'orange':
        return 'Urgent (Orange)';
      case 'yellow':
        return 'Priority (Yellow)';
      case 'green':
      default:
        return 'Routine (Green)';
    }
  };

  const sizeCls = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs';

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full font-bold uppercase tracking-wider border shadow-xs ${sizeCls} ${getStyle()}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
      {getLabel()}
    </span>
  );
};

export default PriorityBadge;
