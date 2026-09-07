import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import Navbar from '../components/Navbar';
import ProgressSteps from '../components/ProgressSteps';
import { usePatient } from '../context/PatientContext';
import { authApi, hospitalApi, consultationApi } from '../api';
import { Hospital } from '../types';
import {
  User,
  Shield,
  Smartphone,
  Mail,
  Fingerprint,
  ArrowRight,
  AlertCircle,
  Building2,
  Lock,
  Calendar,
  Sparkles,
  CheckCircle2,
} from 'lucide-react';

export const IdentifyPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login, setSelectedHospital, setActiveConsultation } = usePatient();

  const [mode, setMode] = useState<'register' | 'login'>('register');
  const [signInMethod, setSignInMethod] = useState<'mobile' | 'abha' | 'email'>('mobile');

  // Hospital directory state
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [selectedHospitalId, setSelectedHospitalId] = useState<string>('');
  const [loadingHospitals, setLoadingHospitals] = useState<boolean>(true);

  // Form Fields
  const [identifier, setIdentifier] = useState('');
  const [loginPassword, setLoginPassword] = useState('');

  // Register Fields
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [dob, setDob] = useState('1990-05-15');
  const [gender, setGender] = useState('Male');
  const [abhaId, setAbhaId] = useState('');
  const [registerPassword, setRegisterPassword] = useState('ClinovaSecure123!');
  const [chiefComplaint, setChiefComplaint] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Load public hospital directory on mount
  useEffect(() => {
    async function loadHospitals() {
      try {
        setLoadingHospitals(true);
        const list = await hospitalApi.listHospitals();
        setHospitals(list);
        if (list.length > 0) {
          setSelectedHospitalId(list[0].id);
        }
      } catch (err: any) {
        console.error('Failed to load hospital directory:', err);
      } finally {
        setLoadingHospitals(false);
      }
    }
    loadHospitals();
  }, []);

  useEffect(() => {
    if (searchParams.get('expired')) {
      setError('Your session has expired. Please sign in again.');
      setMode('login');
    }
  }, [searchParams]);

  // Handle Registration + Consultation creation
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName.trim() || !email.trim() || !selectedHospitalId) {
      setError('Please fill in your name, email, and select your hospital.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // 1. Register
      await authApi.register({
        email: email.trim(),
        password: registerPassword,
        full_name: fullName.trim(),
        phone: phone.trim() || undefined,
        date_of_birth: dob || undefined,
        gender: gender || undefined,
        abha_id: abhaId.trim() || undefined,
      });

      // 2. Login to obtain JWT
      const authRes = await authApi.login({
        identifier: email.trim(),
        password: registerPassword,
      });

      login(authRes);

      // 3. Find selected hospital object
      const hosp = hospitals.find((h) => h.id === selectedHospitalId) || null;
      setSelectedHospital(hosp);

      // 4. Create consultation with selected hospital
      const consult = await consultationApi.createConsultation({
        hospital_id: selectedHospitalId,
        chief_complaint: chiefComplaint.trim() || 'General OPD Consultation',
      });

      setActiveConsultation(consult);

      // 5. Proceed to Consent
      navigate('/consent');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Registration failed. Please check your information.';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

  // Handle Sign In + Consultation creation
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!identifier.trim() || !loginPassword) {
      setError('Please provide your login identifier and password.');
      return;
    }
    if (!selectedHospitalId) {
      setError('Please select the hospital you are visiting today.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // 1. Authenticate
      const authRes = await authApi.login({
        identifier: identifier.trim(),
        password: loginPassword,
      });

      login(authRes);

      // 2. Associate hospital
      const hosp = hospitals.find((h) => h.id === selectedHospitalId) || null;
      setSelectedHospital(hosp);

      // 3. Create consultation encounter for today
      const consult = await consultationApi.createConsultation({
        hospital_id: selectedHospitalId,
        chief_complaint: chiefComplaint.trim() || 'General OPD Follow-up',
      });

      setActiveConsultation(consult);

      // 4. Proceed to Consent
      navigate('/consent');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Invalid credentials. Please try again.';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface flex flex-col">
      <Navbar />

      <main className="max-w-xl w-full mx-auto px-4 py-8 flex-1 flex flex-col justify-start">
        <ProgressSteps currentStepIndex={0} />

        <div className="card-elevated p-6 sm:p-8 bg-surface-container-lowest">
          {/* Header */}
          <div className="flex flex-col items-center text-center mb-6">
            <div className="w-14 h-14 rounded-2xl bg-secondary-container/60 text-secondary flex items-center justify-center mb-3 shadow-xs">
              <User className="w-7 h-7" />
            </div>
            <h1 className="text-2xl font-black text-on-surface tracking-tight">
              Patient Identification
            </h1>
            <p className="text-xs sm:text-sm text-on-surface-variant mt-1">
              Select your hospital facility and identify yourself for OPD intake
            </p>
          </div>

          {/* Error notification */}
          {error && (
            <div className="mb-5 p-3.5 rounded-xl bg-error-container/50 border border-error/30 text-on-error-container text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-error shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Mode Switcher Tabs */}
          <div className="grid grid-cols-2 p-1 rounded-xl bg-surface-container-low mb-6">
            <button
              type="button"
              onClick={() => {
                setMode('register');
                setError('');
              }}
              className={`py-2.5 text-xs font-bold rounded-lg transition-all ${
                mode === 'register'
                  ? 'bg-surface-container-lowest text-primary shadow-xs'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              New Patient
            </button>
            <button
              type="button"
              onClick={() => {
                setMode('login');
                setError('');
              }}
              className={`py-2.5 text-xs font-bold rounded-lg transition-all ${
                mode === 'login'
                  ? 'bg-surface-container-lowest text-primary shadow-xs'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              Existing Sign In
            </button>
          </div>

          {/* Hospital Selection (Authoritative - from GET /api/v1/hospitals) */}
          <div className="mb-5">
            <label className="block text-xs font-bold text-on-surface mb-1.5 flex items-center gap-1.5">
              <Building2 className="w-3.5 h-3.5 text-primary" />
              <span>Select Hospital Facility *</span>
            </label>
            {loadingHospitals ? (
              <div className="w-full h-11 bg-surface-container-low animate-pulse rounded-xl" />
            ) : (
              <select
                value={selectedHospitalId}
                onChange={(e) => setSelectedHospitalId(e.target.value)}
                className="w-full h-11 px-3.5 rounded-xl bg-surface-container-low text-on-surface text-sm border border-outline-variant/50 font-medium cursor-pointer"
                required
              >
                {hospitals.map((h) => (
                  <option key={h.id} value={h.id}>
                    {h.name} {h.city ? `(${h.city}, ${h.state || ''})` : ''}
                  </option>
                ))}
              </select>
            )}
            <span className="text-[11px] text-on-surface-variant mt-1 block">
              Powered by Clinova Hospital Directory API
            </span>
          </div>

          {/* Chief Complaint Input */}
          <div className="mb-5">
            <label className="block text-xs font-bold text-on-surface mb-1.5">
              Primary Symptom / Reason for Visit today
            </label>
            <input
              type="text"
              value={chiefComplaint}
              onChange={(e) => setChiefComplaint(e.target.value)}
              placeholder="e.g. High fever with cough for 3 days"
              className="w-full h-11 px-3.5 rounded-xl bg-surface-container-low text-on-surface text-sm border border-outline-variant/50"
            />
          </div>

          {/* REGISTER FORM */}
          {mode === 'register' && (
            <form onSubmit={handleRegister} className="space-y-4">
              {/* Full Name */}
              <div>
                <label className="block text-xs font-bold text-on-surface mb-1">
                  Full Legal Name *
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Ramesh Kumar"
                  className="w-full h-11 px-3.5 rounded-xl bg-surface-container-low text-on-surface text-sm border border-outline-variant/50"
                  required
                />
              </div>

              {/* Email + Phone */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-on-surface mb-1">
                    Email Address *
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="patient@example.com"
                    className="w-full h-11 px-3.5 rounded-xl bg-surface-container-low text-on-surface text-sm border border-outline-variant/50"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-on-surface mb-1">
                    Mobile Number (optional)
                  </label>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+91 9876543210"
                    className="w-full h-11 px-3.5 rounded-xl bg-surface-container-low text-on-surface text-sm border border-outline-variant/50"
                  />
                </div>
              </div>

              {/* DOB & Gender */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-on-surface mb-1">
                    Date of Birth
                  </label>
                  <input
                    type="date"
                    value={dob}
                    onChange={(e) => setDob(e.target.value)}
                    className="w-full h-11 px-3.5 rounded-xl bg-surface-container-low text-on-surface text-sm border border-outline-variant/50"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-on-surface mb-1">
                    Gender
                  </label>
                  <select
                    value={gender}
                    onChange={(e) => setGender(e.target.value)}
                    className="w-full h-11 px-3.5 rounded-xl bg-surface-container-low text-on-surface text-sm border border-outline-variant/50"
                  >
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>

              {/* ABHA ID with Notice */}
              <div className="p-3 rounded-xl bg-secondary-container/20 border border-secondary-container">
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs font-bold text-secondary flex items-center gap-1.5">
                    <Fingerprint className="w-3.5 h-3.5" />
                    <span>ABHA Health ID (Optional)</span>
                  </label>
                  <span className="text-[10px] font-semibold text-on-surface-variant bg-surface-container px-2 py-0.5 rounded-full">
                    Demographic Identifier
                  </span>
                </div>
                <input
                  type="text"
                  value={abhaId}
                  onChange={(e) => setAbhaId(e.target.value)}
                  placeholder="14-1234-5678-9012"
                  className="w-full h-10 px-3 rounded-lg bg-surface-container-lowest text-on-surface text-sm border border-outline-variant/40"
                />
                <p className="text-[10px] text-on-surface-variant mt-1 leading-normal">
                  Your ABHA ID links previous hospital encounters. Government ABDM gateway exchange is Phase 2.
                </p>
              </div>

              {/* Password */}
              <div>
                <label className="block text-xs font-bold text-on-surface mb-1">
                  Create Password *
                </label>
                <input
                  type="password"
                  value={registerPassword}
                  onChange={(e) => setRegisterPassword(e.target.value)}
                  placeholder="Minimum 8 characters"
                  className="w-full h-11 px-3.5 rounded-xl bg-surface-container-low text-on-surface text-sm border border-outline-variant/50"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full min-h-[48px] mt-4 rounded-xl bg-primary text-on-primary font-bold text-sm shadow-md hover:bg-primary-container transition-all flex items-center justify-center gap-2 cursor-pointer active:scale-98 disabled:opacity-50"
              >
                {loading ? (
                  <span>Registering & Creating Encounter...</span>
                ) : (
                  <>
                    <span>Continue to Informed Consent</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>
          )}

          {/* SIGN IN FORM */}
          {mode === 'login' && (
            <form onSubmit={handleLogin} className="space-y-4">
              {/* Method Tabs */}
              <div className="flex flex-col gap-1.5">
                <span className="text-xs font-bold text-on-surface-variant uppercase tracking-wider">
                  Sign In Using:
                </span>
                <div className="grid grid-cols-3 gap-1.5 p-1 rounded-xl bg-surface-container-low text-xs font-semibold">
                  <button
                    type="button"
                    onClick={() => setSignInMethod('mobile')}
                    className={`py-2 rounded-lg flex items-center justify-center gap-1 transition-all ${
                      signInMethod === 'mobile'
                        ? 'bg-surface-container-lowest text-primary shadow-xs'
                        : 'text-on-surface-variant'
                    }`}
                  >
                    <Smartphone className="w-3.5 h-3.5" />
                    <span>Mobile</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setSignInMethod('abha')}
                    className={`py-2 rounded-lg flex items-center justify-center gap-1 transition-all ${
                      signInMethod === 'abha'
                        ? 'bg-surface-container-lowest text-primary shadow-xs'
                        : 'text-on-surface-variant'
                    }`}
                  >
                    <Fingerprint className="w-3.5 h-3.5" />
                    <span>ABHA ID</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setSignInMethod('email')}
                    className={`py-2 rounded-lg flex items-center justify-center gap-1 transition-all ${
                      signInMethod === 'email'
                        ? 'bg-surface-container-lowest text-primary shadow-xs'
                        : 'text-on-surface-variant'
                    }`}
                  >
                    <Mail className="w-3.5 h-3.5" />
                    <span>Email</span>
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-on-surface mb-1">
                  {signInMethod === 'mobile'
                    ? 'Registered Mobile Number'
                    : signInMethod === 'abha'
                    ? '14-Digit ABHA ID'
                    : 'Email Address'}
                </label>
                <input
                  type="text"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  placeholder={
                    signInMethod === 'mobile'
                      ? '+91 9876543210'
                      : signInMethod === 'abha'
                      ? '14-1234-5678-9012'
                      : 'patient@example.com'
                  }
                  className="w-full h-11 px-3.5 rounded-xl bg-surface-container-low text-on-surface text-sm border border-outline-variant/50"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-on-surface mb-1">
                  Password
                </label>
                <input
                  type="password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  placeholder="Enter your account password"
                  className="w-full h-11 px-3.5 rounded-xl bg-surface-container-low text-on-surface text-sm border border-outline-variant/50"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full min-h-[48px] mt-4 rounded-xl bg-primary text-on-primary font-bold text-sm shadow-md hover:bg-primary-container transition-all flex items-center justify-center gap-2 cursor-pointer active:scale-98 disabled:opacity-50"
              >
                {loading ? (
                  <span>Signing In...</span>
                ) : (
                  <>
                    <span>Sign In & Continue</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>
          )}

          <div className="mt-6 pt-4 border-t border-outline-variant/30 text-center">
            <p className="text-[11px] text-on-surface-variant flex items-center justify-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-secondary" />
              <span>Encrypted JWT Authentication • Role-Enforced PostgreSQL Security</span>
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default IdentifyPage;
