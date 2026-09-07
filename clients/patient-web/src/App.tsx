import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { usePatient } from './context/PatientContext';
import LandingPage from './pages/LandingPage';
import IdentifyPage from './pages/IdentifyPage';
import ConsentPage from './pages/ConsentPage';
import LanguagePage from './pages/LanguagePage';
import InterviewPage from './pages/InterviewPage';
import UploadPage from './pages/UploadPage';
import TimelinePage from './pages/TimelinePage';
import SummaryPage from './pages/SummaryPage';
import EmergencyOverlay from './components/EmergencyOverlay';

// Protected Route Guard
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, activeConsultation } = usePatient();

  if (!isAuthenticated) {
    return <Navigate to="/identify" replace />;
  }

  // If authenticated but no active consultation encounter yet, redirect to identify
  if (!activeConsultation) {
    return <Navigate to="/identify" replace />;
  }

  return <>{children}</>;
};

export const App: React.FC = () => {
  const { triageAlert, setTriageAlert } = usePatient();

  return (
    <div className="min-h-screen bg-surface text-on-surface font-body-md antialiased selection:bg-secondary-container">
      {/* Global Emergency / Red-Flag Triage Overlay */}
      {triageAlert && triageAlert.is_red_flag && (
        <EmergencyOverlay 
          triageResult={triageAlert} 
          onAcknowledge={() => setTriageAlert(null)} 
        />
      )}

      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/identify" element={<IdentifyPage />} />

        {/* Protected Patient Intake Flow */}
        <Route 
          path="/consent" 
          element={
            <ProtectedRoute>
              <ConsentPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/language" 
          element={
            <ProtectedRoute>
              <LanguagePage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/interview" 
          element={
            <ProtectedRoute>
              <InterviewPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/upload" 
          element={
            <ProtectedRoute>
              <UploadPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/timeline" 
          element={
            <ProtectedRoute>
              <TimelinePage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/summary" 
          element={
            <ProtectedRoute>
              <SummaryPage />
            </ProtectedRoute>
          } 
        />

        {/* Catch-all fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
};

export default App;
