import React from 'react';
import { Link } from 'react-router-dom';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center text-center p-6">
      <div className="w-16 h-16 rounded-2xl bg-teal-50 border border-teal-100 flex items-center justify-center text-primary mb-4 shadow-sm">
        <span className="material-symbols-outlined text-3xl">medical_information</span>
      </div>
      <h1 className="text-3xl font-black text-slate-900 tracking-tight">404 — Clinical Record Not Found</h1>
      <p className="text-xs text-slate-500 mt-2 max-w-sm">
        The requested clinical consultation case, patient file, or hospital resource could not be located or access is restricted by hospital isolation policies.
      </p>
      <div className="mt-6 flex items-center gap-3">
        <Link
          to="/dashboard"
          className="px-4 py-2 bg-primary hover:bg-primary-dark text-white text-xs font-bold rounded-xl transition-colors shadow-sm"
        >
          Return to Dashboard
        </Link>
        <Link
          to="/queue"
          className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl transition-colors"
        >
          View OPD Queue
        </Link>
      </div>
    </div>
  );
};
