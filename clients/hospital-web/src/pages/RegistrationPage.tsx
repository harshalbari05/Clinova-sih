import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  lookupPatientByQR,
  confirmRegistration,
  registerManual,
  getDepartments,
} from '../api/reception';
import {
  SafePatientLookup,
  RegistrationResponse,
} from '../types/reception';
import { ErrorAlert } from '../components/common/ErrorAlert';

// Default departments if API is initializing
const FALLBACK_DEPARTMENTS = [
  'General Medicine',
  'Pediatrics',
  'Orthopedics',
  'ENT',
  'Cardiology',
  'Dermatology',
  'Obstetrics & Gynecology',
  'General Surgery',
];

// Department metadata for rich UI display
const DEPARTMENT_META: Record<string, { icon: string; description: string }> = {
  'General Medicine': {
    icon: 'stethoscope',
    description: 'Fever, cough, routine outpatient & acute illness',
  },
  Pediatrics: {
    icon: 'child_care',
    description: 'Infant, child health & vaccination review',
  },
  Orthopedics: {
    icon: 'healing',
    description: 'Bones, fractures, joints & musculoskeletal pain',
  },
  ENT: {
    icon: 'hearing',
    description: 'Ear, nose, throat & seasonal allergy care',
  },
  Cardiology: {
    icon: 'favorite',
    description: 'Hypertension, chest discomfort & cardiac follow-up',
  },
  Dermatology: {
    icon: 'spa',
    description: 'Skin rashes, lesions, eczema & infections',
  },
  'Obstetrics & Gynecology': {
    icon: 'pregnant_woman',
    description: 'Maternal health, prenatal & women wellness',
  },
  'General Surgery': {
    icon: 'medical_services',
    description: 'Pre-op triage, acute abdominal pain & wound care',
  },
};

type Mode = 'qr' | 'manual';

export const RegistrationPage: React.FC = () => {
  const { hospital, hospitalRole } = useAuth();
  const navigate = useNavigate();

  // Mode and step
  const [mode, setMode] = useState<Mode>('qr');
  const [step, setStep] = useState<'input' | 'confirm' | 'success'>('input');

  // Department catalog
  const [departments, setDepartments] = useState<string[]>(FALLBACK_DEPARTMENTS);
  const [selectedDepartment, setSelectedDepartment] = useState<string>('');

  // Patient data from QR
  const [scannedPatient, setScannedPatient] = useState<SafePatientLookup | null>(null);

  // Manual form state
  const [manualForm, setManualForm] = useState({
    fullName: '',
    phone: '',
    age: '',
    gender: 'Male',
    abhaId: '',
    chiefComplaint: '',
  });

  // Success state
  const [registrationResult, setRegistrationResult] = useState<RegistrationResponse | null>(null);

  // Loading & Error
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // QR input field (supports manual paste / USB barcode gun / fast typing)
  const [qrInput, setQrInput] = useState('');

  // Camera scanner state
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const scanIntervalRef = useRef<number | null>(null);

  // Load departments on mount
  useEffect(() => {
    async function loadDepts() {
      try {
        const list = await getDepartments();
        if (list && list.length > 0) {
          setDepartments(list);
        }
      } catch {
        // Keep fallback departments
      }
    }
    loadDepts();
  }, []);

  // Clean up camera on unmount or mode switch
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  const startCamera = async () => {
    setCameraError(null);
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Camera device access is not supported by this browser.');
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 640 }, height: { ideal: 480 } },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setIsCameraActive(true);

      // BarcodeDetector setup if available
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const BarcodeDetectorClass = (window as any).BarcodeDetector;
      if (BarcodeDetectorClass) {
        const detector = new BarcodeDetectorClass({ formats: ['qr_code'] });
        const interval = window.setInterval(async () => {
          if (videoRef.current && videoRef.current.readyState >= 2) {
            try {
              const barcodes = await detector.detect(videoRef.current);
              if (barcodes && barcodes.length > 0) {
                const rawValue = barcodes[0].rawValue;
                if (rawValue) {
                  stopCamera();
                  handleLookup(rawValue);
                }
              }
            } catch {
              // Ignore frame detection errors
            }
          }
        }, 500);
        scanIntervalRef.current = interval;
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to access camera.';
      setCameraError(msg);
      setIsCameraActive(false);
    }
  };

  const stopCamera = () => {
    if (scanIntervalRef.current) {
      clearInterval(scanIntervalRef.current);
      scanIntervalRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setIsCameraActive(false);
  };

  // Perform QR lookup via API
  const handleLookup = async (code: string) => {
    const trimmed = code.trim();
    if (!trimmed) {
      setError('Please provide a valid Clinova Patient QR code.');
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const patient = await lookupPatientByQR(trimmed);
      setScannedPatient(patient);
      setSelectedDepartment(departments[0] || 'General Medicine');
      setStep('confirm');
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const apiErr = err as any;
      const detail =
        apiErr.response?.data?.detail ||
        (err instanceof Error ? err.message : 'Unable to find patient from this QR code.');
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  // Confirm registration from QR
  const handleConfirmQRRegistration = async () => {
    if (!scannedPatient) return;
    if (!selectedDepartment) {
      setError('Please select an OPD department for this patient visit.');
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const res = await confirmRegistration({
        patient_id: scannedPatient.patient_id,
        department: selectedDepartment,
        consultation_id: scannedPatient.active_consultation_id,
      });
      setRegistrationResult(res);
      setStep('success');
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const apiErr = err as any;
      const detail =
        apiErr.response?.data?.detail ||
        (err instanceof Error ? err.message : 'Registration failed. Please try again.');
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  // Submit manual registration
  const handleManualRegistration = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualForm.fullName.trim()) {
      setError('Patient Full Name is required.');
      return;
    }
    if (!manualForm.phone.trim()) {
      setError('Mobile Number is required for patient tracking.');
      return;
    }
    if (!selectedDepartment) {
      setError('Please select an OPD department.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const ageNum = manualForm.age ? parseInt(manualForm.age, 10) : undefined;
      const res = await registerManual({
        full_name: manualForm.fullName.trim(),
        phone: manualForm.phone.trim(),
        age: !isNaN(ageNum as number) ? ageNum : undefined,
        gender: manualForm.gender,
        abha_id: manualForm.abhaId.trim() || undefined,
        department: selectedDepartment,
        chief_complaint: manualForm.chiefComplaint.trim() || undefined,
      });
      setRegistrationResult(res);
      setStep('success');
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const apiErr = err as any;
      const detail =
        apiErr.response?.data?.detail ||
        (err instanceof Error ? err.message : 'Manual registration failed.');
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  // Reset to register next patient
  const handleReset = () => {
    stopCamera();
    setStep('input');
    setScannedPatient(null);
    setSelectedDepartment(departments[0] || 'General Medicine');
    setQrInput('');
    setManualForm({
      fullName: '',
      phone: '',
      age: '',
      gender: 'Male',
      abhaId: '',
      chiefComplaint: '',
    });
    setRegistrationResult(null);
    setError(null);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header Banner */}
      <div className="bg-surface-container-lowest rounded-2xl border border-outline-variant/30 p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-primary/10 text-primary border border-primary/20">
              Hospital Reception Desk
            </span>
            <span className="text-xs text-on-surface-variant">
              • {hospital?.name || 'Main OPD Registration'}
            </span>
          </div>
          <h1 className="text-2xl font-black text-on-surface tracking-tight">
            Patient Visit Registration
          </h1>
          <p className="text-xs text-on-surface-variant mt-1 max-w-xl">
            Scan patient’s Clinova QR code to register their hospital visit and route to an OPD
            department. Medical summaries and clinical history remain strictly private.
          </p>
        </div>

        {/* Mode Switcher */}
        {step === 'input' && (
          <div className="flex items-center bg-surface-container rounded-xl p-1 shrink-0 border border-outline-variant/30">
            <button
              type="button"
              onClick={() => {
                setMode('qr');
                setError(null);
              }}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold transition-all ${
                mode === 'qr'
                  ? 'bg-surface-container-lowest text-primary shadow-xs'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">qr_code_scanner</span>
              <span>Scan QR</span>
            </button>
            <button
              type="button"
              onClick={() => {
                stopCamera();
                setMode('manual');
                setError(null);
                setSelectedDepartment(departments[0] || 'General Medicine');
              }}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold transition-all ${
                mode === 'manual'
                  ? 'bg-surface-container-lowest text-primary shadow-xs'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">edit_note</span>
              <span>Manual Entry</span>
            </button>
          </div>
        )}
      </div>

      {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

      {/* STEP 1: SCAN QR MODE */}
      {step === 'input' && mode === 'qr' && (
        <div className="space-y-6">
          {/* QR Scanner Card */}
          <div className="bg-surface-container-lowest rounded-2xl border border-outline-variant/30 p-6 shadow-xs">
            <div className="flex flex-col items-center justify-center text-center space-y-4">
              {/* Camera Scanner View */}
              {isCameraActive ? (
                <div className="relative w-full max-w-md aspect-video bg-black rounded-2xl overflow-hidden border-2 border-primary shadow-inner">
                  <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className="w-full h-full object-cover"
                  />
                  {/* Targeting reticle */}
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div className="w-48 h-48 border-2 border-dashed border-primary-fixed rounded-2xl animate-pulse flex items-center justify-center">
                      <span className="text-white text-xs font-semibold bg-black/60 px-3 py-1 rounded-full">
                        Point at Patient QR
                      </span>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={stopCamera}
                    className="absolute top-3 right-3 bg-black/70 hover:bg-black text-white p-2 rounded-full text-xs font-bold"
                    title="Stop Camera"
                  >
                    <span className="material-symbols-outlined text-[16px]">close</span>
                  </button>
                </div>
              ) : (
                <div className="w-20 h-20 rounded-2xl bg-primary/10 text-primary flex items-center justify-center">
                  <span className="material-symbols-outlined text-[44px]">qr_code_scanner</span>
                </div>
              )}

              {!isCameraActive && (
                <div className="max-w-md">
                  <h3 className="text-base font-bold text-on-surface">
                    Scan Patient Clinova QR
                  </h3>
                  <p className="text-xs text-on-surface-variant mt-1">
                    Ask the patient to display their Clinova QR code on their phone screen.
                  </p>
                </div>
              )}

              {cameraError && (
                <div className="text-xs text-error bg-error-container/30 px-3 py-1.5 rounded-lg border border-error/20">
                  {cameraError}
                </div>
              )}

              {/* Camera Toggle Button */}
              <div className="flex flex-wrap items-center justify-center gap-3">
                {!isCameraActive ? (
                  <button
                    type="button"
                    onClick={startCamera}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-container text-on-primary font-bold text-xs shadow-xs transition-all"
                  >
                    <span className="material-symbols-outlined text-[18px]">photo_camera</span>
                    <span>Start Webcam Scanner</span>
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={stopCamera}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-surface-container-high text-on-surface font-semibold text-xs"
                  >
                    <span className="material-symbols-outlined text-[16px]">stop</span>
                    <span>Stop Camera</span>
                  </button>
                )}
              </div>

              {/* Barcode Gun / Manual Input Fallback */}
              <div className="w-full max-w-md pt-4 border-t border-outline-variant/20">
                <label className="block text-left text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-1.5">
                  Or Scan with USB Scanner / Paste QR Code
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={qrInput}
                    onChange={(e) => setQrInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleLookup(qrInput);
                      }
                    }}
                    placeholder="CLINOVA:PATIENT:..."
                    className="flex-1 px-3.5 py-2.5 bg-surface-container-low border border-outline-variant/40 rounded-xl text-xs text-on-surface font-mono placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  />
                  <button
                    type="button"
                    disabled={loading || !qrInput.trim()}
                    onClick={() => handleLookup(qrInput)}
                    className="px-4 py-2.5 rounded-xl bg-secondary text-on-secondary font-bold text-xs hover:bg-secondary-container hover:text-on-secondary-container transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
                  >
                    {loading ? (
                      <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                      <>
                        <span>Lookup</span>
                        <span className="material-symbols-outlined text-[16px]">search</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Fallback switch prompt */}
              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => {
                    stopCamera();
                    setMode('manual');
                    setError(null);
                    setSelectedDepartment(departments[0] || 'General Medicine');
                  }}
                  className="text-xs font-semibold text-primary hover:underline inline-flex items-center gap-1"
                >
                  <span className="material-symbols-outlined text-[14px]">help</span>
                  <span>QR not working? Enter details manually</span>
                </button>
              </div>
            </div>
          </div>

          {/* Quick Demo Simulator Section (SIH Demo First) */}
          <div className="bg-surface-container-low/70 border border-outline-variant/30 rounded-2xl p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-[18px]">bolt</span>
                <span className="text-xs font-bold text-on-surface uppercase tracking-wider">
                  SIH Quick Demo: Instant QR Simulator
                </span>
              </div>
              <span className="text-[11px] text-on-surface-variant">
                1-click simulation for judges & presentation
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() =>
                  handleLookup('CLINOVA:PATIENT:dcc17922-076e-4187-a23f-015ed6c7b9ac')
                }
                disabled={loading}
                className="text-left p-3.5 rounded-xl bg-surface-container-lowest border border-outline-variant/40 hover:border-primary hover:shadow-xs transition-all flex items-center justify-between group"
              >
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-xs text-on-surface group-hover:text-primary">
                      Rohan Patil
                    </span>
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-primary/10 text-primary">
                      Pre-Hospital Intake
                    </span>
                  </div>
                  <div className="text-[11px] text-on-surface-variant mt-0.5">
                    34 Y / Male • 9876543210 • ABHA: 12-3456-7890-1234
                  </div>
                </div>
                <span className="material-symbols-outlined text-[18px] text-on-surface-variant group-hover:text-primary">
                  qr_code
                </span>
              </button>

              <button
                type="button"
                onClick={() =>
                  handleLookup('CLINOVA:PATIENT:6444d0e4-e9a1-4266-b221-896dbd50f877')
                }
                disabled={loading}
                className="text-left p-3.5 rounded-xl bg-surface-container-lowest border border-outline-variant/40 hover:border-primary hover:shadow-xs transition-all flex items-center justify-between group"
              >
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-xs text-on-surface group-hover:text-primary">
                      Ananya Deshmukh
                    </span>
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-tertiary/10 text-tertiary">
                      Verified Profile
                    </span>
                  </div>
                  <div className="text-[11px] text-on-surface-variant mt-0.5">
                    56 Y / Female • 9812345678 • ABHA: 98-7654-3210-9876
                  </div>
                </div>
                <span className="material-symbols-outlined text-[18px] text-on-surface-variant group-hover:text-primary">
                  qr_code
                </span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* STEP 2: CONFIRM SCANNED PATIENT & SELECT OPD DEPARTMENT */}
      {step === 'confirm' && scannedPatient && (
        <div className="space-y-6">
          {/* Patient Demographic Profile Card (Strictly non-clinical) */}
          <div className="bg-surface-container-lowest rounded-2xl border border-outline-variant/30 p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-outline-variant/20 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold text-lg">
                  {scannedPatient.full_name.charAt(0)}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-primary bg-primary/10 px-2 py-0.5 rounded-full">
                      Patient Identified
                    </span>
                    {scannedPatient.has_active_intake && (
                      <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-800 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full flex items-center gap-1">
                        <span className="material-symbols-outlined text-[12px]">smart_toy</span>
                        Pre-Hospital AI Intake Completed
                      </span>
                    )}
                  </div>
                  <h2 className="text-xl font-bold text-on-surface mt-0.5">
                    {scannedPatient.full_name}
                  </h2>
                </div>
              </div>

              <button
                type="button"
                onClick={handleReset}
                className="text-xs text-on-surface-variant hover:text-on-surface flex items-center gap-1"
              >
                <span className="material-symbols-outlined text-[16px]">close</span>
                <span>Scan Different Patient</span>
              </button>
            </div>

            {/* Demographics Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-1">
              <div className="p-3 bg-surface-container-low rounded-xl">
                <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant block">
                  Age / Gender
                </span>
                <span className="text-sm font-bold text-on-surface mt-0.5 block">
                  {scannedPatient.age ? `${scannedPatient.age} Y` : 'N/A'} •{' '}
                  {scannedPatient.gender || 'Not specified'}
                </span>
              </div>

              <div className="p-3 bg-surface-container-low rounded-xl">
                <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant block">
                  Mobile Number
                </span>
                <span className="text-sm font-bold text-on-surface mt-0.5 block">
                  {scannedPatient.phone || 'Not recorded'}
                </span>
              </div>

              <div className="p-3 bg-surface-container-low rounded-xl">
                <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant block">
                  ABHA ID
                </span>
                <span className="text-sm font-bold text-on-surface mt-0.5 block truncate">
                  {scannedPatient.abha_id || 'Not linked'}
                </span>
              </div>

              <div className="p-3 bg-surface-container-low rounded-xl">
                <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant block">
                  Patient Ref
                </span>
                <span className="text-sm font-mono font-bold text-on-surface mt-0.5 block truncate">
                  #{scannedPatient.patient_id.slice(0, 8)}
                </span>
              </div>
            </div>

            {/* Strict Privacy Shield Notice */}
            <div className="flex items-start gap-2.5 p-3 rounded-xl bg-surface-container-low/70 border border-outline-variant/30 text-xs text-on-surface-variant">
              <span className="material-symbols-outlined text-primary text-[18px] shrink-0 mt-0.5">
                verified_user
              </span>
              <div>
                <span className="font-bold text-on-surface">Data Protection Guarantee: </span>
                Clinical summary, interview transcript, medications, and medical documents are
                confidential. They are sealed and accessible only by attending doctors during
                consultation.
              </div>
            </div>
          </div>

          {/* Department Selection Grid */}
          <div className="bg-surface-container-lowest rounded-2xl border border-outline-variant/30 p-6 shadow-xs space-y-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-primary text-on-primary text-xs font-bold flex items-center justify-center">
                  2
                </span>
                <h3 className="text-base font-bold text-on-surface">
                  Assign OPD Department for this Visit
                </h3>
              </div>
              <p className="text-xs text-on-surface-variant mt-1 ml-7">
                Receptionist selects exactly one department. The patient will be queued for
                consultation in this department.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 ml-0 sm:ml-7">
              {departments.map((dept) => {
                const isSelected = selectedDepartment === dept;
                const meta = DEPARTMENT_META[dept] || {
                  icon: 'local_hospital',
                  description: 'General outpatient department',
                };

                return (
                  <button
                    key={dept}
                    type="button"
                    onClick={() => setSelectedDepartment(dept)}
                    className={`text-left p-4 rounded-xl border-2 transition-all flex flex-col justify-between min-h-[110px] ${
                      isSelected
                        ? 'border-primary bg-primary/5 shadow-xs'
                        : 'border-outline-variant/30 bg-surface-container-low hover:border-outline hover:bg-surface-container'
                    }`}
                  >
                    <div className="flex items-start justify-between w-full">
                      <span
                        className={`material-symbols-outlined text-[24px] ${
                          isSelected ? 'text-primary' : 'text-on-surface-variant'
                        }`}
                      >
                        {meta.icon}
                      </span>
                      {isSelected && (
                        <span className="w-5 h-5 rounded-full bg-primary text-on-primary flex items-center justify-center">
                          <span className="material-symbols-outlined text-[14px]">check</span>
                        </span>
                      )}
                    </div>
                    <div className="mt-2">
                      <span
                        className={`block text-xs font-bold ${
                          isSelected ? 'text-primary' : 'text-on-surface'
                        }`}
                      >
                        {dept}
                      </span>
                      <span className="block text-[10px] text-on-surface-variant mt-0.5 leading-tight">
                        {meta.description}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Registration Action Buttons */}
            <div className="pt-4 border-t border-outline-variant/20 flex flex-col sm:flex-row items-center justify-end gap-3">
              <button
                type="button"
                onClick={handleReset}
                disabled={loading}
                className="w-full sm:w-auto px-5 py-2.5 rounded-xl border border-outline-variant text-xs font-bold text-on-surface-variant hover:bg-surface-container transition-all"
              >
                Cancel / Reset
              </button>

              <button
                type="button"
                disabled={loading || !selectedDepartment}
                onClick={handleConfirmQRRegistration}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl bg-primary hover:bg-primary-container text-on-primary font-bold text-xs shadow-md shadow-primary/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <>
                    <span>Confirm & Register to {selectedDepartment}</span>
                    <span className="material-symbols-outlined text-[18px]">how_to_reg</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* STEP 1 (FALLBACK): MANUAL WALK-IN REGISTRATION FORM */}
      {step === 'input' && mode === 'manual' && (
        <form
          onSubmit={handleManualRegistration}
          className="bg-surface-container-lowest rounded-2xl border border-outline-variant/30 p-6 shadow-xs space-y-6"
        >
          <div className="border-b border-outline-variant/20 pb-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-amber-800 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full">
                  Manual Fallback
                </span>
                <h2 className="text-lg font-bold text-on-surface mt-1">
                  Walk-in Patient Registration
                </h2>
                <p className="text-xs text-on-surface-variant mt-0.5">
                  Enter minimum required details for this visit when patient has no QR code. No
                  profile search is performed.
                </p>
              </div>

              <button
                type="button"
                onClick={() => {
                  setMode('qr');
                  setError(null);
                }}
                className="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
              >
                <span className="material-symbols-outlined text-[16px]">qr_code_scanner</span>
                <span>Switch to QR Scanner</span>
              </button>
            </div>
          </div>

          {/* Form Fields */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Full Name */}
            <div>
              <label className="block text-xs font-bold text-on-surface uppercase tracking-wider mb-1">
                Full Name <span className="text-error">*</span>
              </label>
              <input
                type="text"
                required
                value={manualForm.fullName}
                onChange={(e) => setManualForm({ ...manualForm, fullName: e.target.value })}
                placeholder="e.g. Ramesh Kumar"
                className="w-full px-3.5 py-2.5 bg-surface-container-low border border-outline-variant/40 rounded-xl text-xs text-on-surface focus:outline-none focus:border-primary"
              />
            </div>

            {/* Phone */}
            <div>
              <label className="block text-xs font-bold text-on-surface uppercase tracking-wider mb-1">
                Mobile Number <span className="text-error">*</span>
              </label>
              <input
                type="tel"
                required
                maxLength={10}
                value={manualForm.phone}
                onChange={(e) => setManualForm({ ...manualForm, phone: e.target.value })}
                placeholder="10-digit mobile number"
                className="w-full px-3.5 py-2.5 bg-surface-container-low border border-outline-variant/40 rounded-xl text-xs text-on-surface focus:outline-none focus:border-primary"
              />
            </div>

            {/* Age */}
            <div>
              <label className="block text-xs font-bold text-on-surface uppercase tracking-wider mb-1">
                Age (Years)
              </label>
              <input
                type="number"
                min={0}
                max={125}
                value={manualForm.age}
                onChange={(e) => setManualForm({ ...manualForm, age: e.target.value })}
                placeholder="e.g. 42"
                className="w-full px-3.5 py-2.5 bg-surface-container-low border border-outline-variant/40 rounded-xl text-xs text-on-surface focus:outline-none focus:border-primary"
              />
            </div>

            {/* Gender */}
            <div>
              <label className="block text-xs font-bold text-on-surface uppercase tracking-wider mb-1">
                Gender
              </label>
              <select
                value={manualForm.gender}
                onChange={(e) => setManualForm({ ...manualForm, gender: e.target.value })}
                className="w-full px-3.5 py-2.5 bg-surface-container-low border border-outline-variant/40 rounded-xl text-xs text-on-surface focus:outline-none focus:border-primary"
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>

            {/* ABHA ID (Optional) */}
            <div>
              <label className="block text-xs font-bold text-on-surface uppercase tracking-wider mb-1">
                ABHA ID <span className="text-on-surface-variant font-normal">(Optional)</span>
              </label>
              <input
                type="text"
                value={manualForm.abhaId}
                onChange={(e) => setManualForm({ ...manualForm, abhaId: e.target.value })}
                placeholder="e.g. 12-3456-7890-1234"
                className="w-full px-3.5 py-2.5 bg-surface-container-low border border-outline-variant/40 rounded-xl text-xs text-on-surface focus:outline-none focus:border-primary"
              />
            </div>

            {/* Chief Complaint (Brief Note) */}
            <div>
              <label className="block text-xs font-bold text-on-surface uppercase tracking-wider mb-1">
                Primary Complaint / Reason for Visit
              </label>
              <input
                type="text"
                value={manualForm.chiefComplaint}
                onChange={(e) => setManualForm({ ...manualForm, chiefComplaint: e.target.value })}
                placeholder="e.g. Fever for 3 days, body ache"
                className="w-full px-3.5 py-2.5 bg-surface-container-low border border-outline-variant/40 rounded-xl text-xs text-on-surface focus:outline-none focus:border-primary"
              />
            </div>
          </div>

          {/* Department Selection Grid */}
          <div className="pt-2">
            <label className="block text-xs font-bold text-on-surface uppercase tracking-wider mb-2">
              Select OPD Department <span className="text-error">*</span>
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {departments.map((dept) => {
                const isSelected = selectedDepartment === dept;
                const meta = DEPARTMENT_META[dept] || {
                  icon: 'local_hospital',
                  description: 'General outpatient department',
                };

                return (
                  <button
                    key={dept}
                    type="button"
                    onClick={() => setSelectedDepartment(dept)}
                    className={`text-left p-3.5 rounded-xl border-2 transition-all flex flex-col justify-between min-h-[95px] ${
                      isSelected
                        ? 'border-primary bg-primary/5 shadow-xs'
                        : 'border-outline-variant/30 bg-surface-container-low hover:border-outline'
                    }`}
                  >
                    <div className="flex items-start justify-between w-full">
                      <span
                        className={`material-symbols-outlined text-[22px] ${
                          isSelected ? 'text-primary' : 'text-on-surface-variant'
                        }`}
                      >
                        {meta.icon}
                      </span>
                      {isSelected && (
                        <span className="w-4 h-4 rounded-full bg-primary text-on-primary flex items-center justify-center">
                          <span className="material-symbols-outlined text-[12px]">check</span>
                        </span>
                      )}
                    </div>
                    <div className="mt-1">
                      <span
                        className={`block text-xs font-bold ${
                          isSelected ? 'text-primary' : 'text-on-surface'
                        }`}
                      >
                        {dept}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Submit Actions */}
          <div className="pt-4 border-t border-outline-variant/20 flex flex-col sm:flex-row items-center justify-end gap-3">
            <button
              type="button"
              onClick={() => {
                setMode('qr');
                setError(null);
              }}
              disabled={loading}
              className="w-full sm:w-auto px-5 py-2.5 rounded-xl border border-outline-variant text-xs font-bold text-on-surface-variant hover:bg-surface-container"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !manualForm.fullName.trim() || !manualForm.phone.trim() || !selectedDepartment}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl bg-primary hover:bg-primary-container text-on-primary font-bold text-xs shadow-md shadow-primary/20 transition-all disabled:opacity-50"
            >
              {loading ? (
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <span>Register Walk-in Patient</span>
                  <span className="material-symbols-outlined text-[18px]">how_to_reg</span>
                </>
              )}
            </button>
          </div>
        </form>
      )}

      {/* STEP 3: REGISTRATION SUCCESS BANNER */}
      {step === 'success' && registrationResult && (
        <div className="bg-surface-container-lowest rounded-2xl border border-outline-variant/30 p-8 shadow-xs text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto shadow-inner">
            <span className="material-symbols-outlined text-[36px]">check_circle</span>
          </div>

          <div className="max-w-md mx-auto space-y-1">
            <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-50 text-emerald-800 border border-emerald-200">
              Registration Successful
            </span>
            <h2 className="text-2xl font-black text-on-surface mt-2">
              {registrationResult.patient_name}
            </h2>
            <p className="text-xs text-on-surface-variant">
              Successfully registered and assigned to OPD consultation.
            </p>
          </div>

          {/* Generated OPD Token Card */}
          <div className="max-w-md mx-auto bg-primary/10 border-2 border-primary/30 rounded-2xl p-5 flex items-center justify-between shadow-xs">
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-primary block">
                Generated OPD Token
              </span>
              <span className="text-xs font-semibold text-on-surface-variant">
                {registrationResult.department} Queue
              </span>
            </div>
            <div className="text-4xl font-black text-primary font-mono tracking-tight bg-surface-container-lowest px-5 py-2 rounded-xl border border-primary/20 shadow-xs">
              #{registrationResult.token_number}
            </div>
          </div>

          {/* Registration Details Summary */}
          <div className="max-w-md mx-auto bg-surface-container-low rounded-2xl p-5 text-left space-y-3 border border-outline-variant/30">
            <div className="flex items-center justify-between border-b border-outline-variant/20 pb-2">
              <span className="text-xs text-on-surface-variant font-medium">Assigned Department</span>
              <span className="text-xs font-bold text-primary px-2.5 py-0.5 rounded-full bg-primary/10">
                {registrationResult.department}
              </span>
            </div>
            <div className="flex items-center justify-between border-b border-outline-variant/20 pb-2">
              <span className="text-xs text-on-surface-variant font-medium">Hospital Facility</span>
              <span className="text-xs font-bold text-on-surface">
                {registrationResult.hospital_name}
              </span>
            </div>
            <div className="flex items-center justify-between border-b border-outline-variant/20 pb-2">
              <span className="text-xs text-on-surface-variant font-medium">Visit Consultation ID</span>
              <span className="text-xs font-mono font-bold text-on-surface">
                #{registrationResult.consultation_id.slice(0, 8)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-on-surface-variant font-medium">Queue Status</span>
              <span className="text-xs font-bold text-amber-700 uppercase">
                {registrationResult.status}
              </span>
            </div>
          </div>

          {/* Follow-up actions */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
            <button
              type="button"
              onClick={handleReset}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl bg-primary hover:bg-primary-container text-on-primary font-bold text-xs shadow-md shadow-primary/20 transition-all"
            >
              <span className="material-symbols-outlined text-[18px]">person_add</span>
              <span>Register Next Patient</span>
            </button>

            <button
              type="button"
              onClick={() => navigate('/queue')}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl border border-outline-variant text-xs font-bold text-on-surface hover:bg-surface-container transition-all"
            >
              <span className="material-symbols-outlined text-[18px]">format_list_numbered</span>
              <span>View in OPD Queue</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
