import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { usePatient } from '../context/PatientContext';
import { Activity, LogOut, User as UserIcon, Building2 } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { isAuthenticated, patient, user, selectedHospital, logout } = usePatient();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <header className="sticky top-0 z-40 bg-surface/90 backdrop-blur-xl border-b border-outline-variant/30 shadow-[0_1px_8px_rgba(0,0,0,0.04)] pt-safe">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Brand Logo */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="w-10 h-10 rounded-xl bg-primary text-on-primary flex items-center justify-center shadow-sm group-hover:bg-primary-container transition-colors">
            <Activity className="w-5 h-5" />
          </div>
          <div className="flex flex-col">
            <span className="font-bold text-xl tracking-tight text-primary leading-none">
              CLINOVA
            </span>
            <span className="text-[11px] font-semibold text-on-surface-variant uppercase tracking-wider">
              Smart Clinical Intake
            </span>
          </div>
        </Link>

        {/* Center / Hospital facility info if selected */}
        {selectedHospital && (
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-secondary-container/40 text-on-secondary-container text-xs font-semibold">
            <Building2 className="w-3.5 h-3.5 text-secondary" />
            <span className="truncate max-w-[200px]">{selectedHospital.name}</span>
            {selectedHospital.city && (
              <span className="text-on-surface-variant font-normal">• {selectedHospital.city}</span>
            )}
          </div>
        )}

        {/* Right action items */}
        <div className="flex items-center gap-3">
          {isAuthenticated && patient ? (
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-container text-on-surface text-xs font-medium">
                <div className="w-6 h-6 rounded-full bg-primary/10 text-primary flex items-center justify-center">
                  <UserIcon className="w-3.5 h-3.5" />
                </div>
                <span className="font-semibold text-on-surface max-w-[120px] truncate">
                  {patient.full_name}
                </span>
              </div>
              <button
                onClick={handleLogout}
                className="p-2 rounded-xl text-error hover:bg-error-container/30 transition-colors"
                title="Sign Out"
                aria-label="Sign Out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <Link
              to="/identify"
              className="px-4 py-2 rounded-xl bg-primary text-on-primary text-xs font-bold hover:bg-primary-container transition-colors shadow-sm"
            >
              Sign In
            </Link>
          )}
        </div>
      </div>
    </header>
  );
};

export default Navbar;
