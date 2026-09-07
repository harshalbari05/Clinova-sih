import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';

export const Header: React.FC = () => {
  const { user, hospital, hospitalRole, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const displayName = user?.full_name || 'Dr. Amit Sharma';
  const hospitalName = hospital?.name || 'City Hospital • OPD Wing B';
  const roleLabel = hospitalRole === 'hospital_admin' ? 'Hospital Administrator' : 'Consultant Physician, Gen Med';

  return (
    <header className="fixed top-0 left-0 right-0 h-16 bg-surface-container-lowest border-b border-outline-variant/30 z-50 flex items-center justify-between px-6 md:px-8">
      {/* Left Branding & Station Context */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-on-primary">
            <span className="material-symbols-outlined text-[20px]">local_hospital</span>
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-bold text-on-surface tracking-tight leading-none">CLINOVA</span>
            <span className="text-[11px] text-on-surface-variant leading-tight">Doctor Workstation</span>
          </div>
        </div>

        <div className="h-6 w-px bg-outline-variant/40 hidden md:block" />

        <div className="hidden md:flex items-center gap-2">
          <span className="bg-surface-container-high text-on-surface px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-primary" />
            {hospitalName}
          </span>
          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-secondary-container/60 text-on-secondary-container rounded-full text-xs font-medium">
            <span className="w-2 h-2 rounded-full bg-secondary animate-pulse" />
            On Duty • Room 104
          </div>
        </div>
      </div>

      {/* Right User & Actions */}
      <div className="flex items-center gap-4">
        {/* User Info Badge */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-secondary-container text-on-secondary-container flex items-center justify-center font-bold text-xs">
            {displayName.slice(0, 2).toUpperCase()}
          </div>
          <div className="hidden lg:flex flex-col text-left">
            <span className="text-xs font-semibold text-on-surface leading-tight">{displayName}</span>
            <span className="text-[11px] text-on-surface-variant leading-tight">{roleLabel}</span>
          </div>
        </div>

        <div className="h-6 w-px bg-outline-variant/40" />

        {/* Logout Button */}
        <button
          onClick={handleLogout}
          className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-on-surface-variant hover:bg-error-container/40 hover:text-on-error-container transition-colors text-xs font-medium"
          type="button"
          aria-label="Logout"
        >
          <span className="material-symbols-outlined text-[18px]">logout</span>
          <span className="hidden sm:inline">Logout</span>
        </button>
      </div>
    </header>
  );
};
