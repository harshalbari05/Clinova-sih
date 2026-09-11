import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

interface SidebarProps {
  queueCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ queueCount }) => {
  const { hospitalRole } = useAuth();
  const isReceptionist = hospitalRole === 'receptionist';

  const navItems = [
    { to: '/dashboard', label: 'Dashboard', icon: 'grid_view' },
    { to: '/registration', label: 'Patient Registration', icon: 'how_to_reg' },
    { to: '/queue', label: 'OPD Queue', icon: 'format_list_numbered', badge: queueCount },
    ...(!isReceptionist
      ? [{ to: '/documents', label: 'Medical Documents', icon: 'folder_shared' }]
      : []),
  ];

  return (
    <aside className="fixed left-0 top-16 bottom-0 w-64 bg-surface-container-lowest border-r border-outline-variant/30 z-40 flex flex-col justify-between p-4">
      {/* Navigation Group */}
      <div className="flex flex-col gap-2">
        <div className="px-3 py-1 mb-1">
          <span className="text-[11px] text-on-surface-variant uppercase tracking-wider font-semibold">
            Clinical Navigation
          </span>
        </div>

        <nav className="flex flex-col gap-1.5" aria-label="Main Clinical Navigation">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-primary text-on-primary font-bold shadow-sm'
                    : 'text-on-surface-variant hover:bg-surface-container hover:text-on-surface'
                }`
              }
            >
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
                <span>{item.label}</span>
              </div>
              {item.badge !== undefined && item.badge > 0 && (
                <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-primary-fixed text-on-primary-fixed">
                  {item.badge}
                </span>
              )}
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Support & Compliance Footer */}
      <div className="pt-4 border-t border-outline-variant/30 flex flex-col gap-3">
        <div className="bg-surface-container-low rounded-xl p-3 flex flex-col gap-1">
          <div className="flex items-center gap-1.5 text-on-surface text-xs font-semibold">
            <span className="material-symbols-outlined text-[16px] text-primary">support_agent</span>
            Clinical Desk Support
          </div>
          <span className="text-[11px] text-on-surface-variant">Ext: 4402 | Op Speeddial 9</span>
        </div>

        <div className="px-2 flex items-center justify-between text-on-surface-variant text-[11px]">
          <span>NABH Accredited</span>
          <span className="font-semibold text-primary">v2.4</span>
        </div>
      </div>
    </aside>
  );
};
