import React from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

interface HospitalLayoutProps {
  queueCount?: number;
}

export const HospitalLayout: React.FC<HospitalLayoutProps> = ({ queueCount }) => {
  return (
    <div className="min-h-screen bg-background text-on-surface">
      <Header />
      <Sidebar queueCount={queueCount} />
      <main className="pl-64 pt-16 min-h-screen">
        <div className="p-6 md:p-8 max-w-7xl mx-auto w-full">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
