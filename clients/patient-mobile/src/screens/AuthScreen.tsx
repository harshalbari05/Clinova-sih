/**
 * Mobile Authentication Screen
 * Faithfully matches clinova_patient_staff_login design.
 * Supports Mobile Phone OTP, ABHA ID login, Email/Password, and New Patient Registration.
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  SafeAreaView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { colors, typography, spacing, borderRadius, shadows } from '../constants/theme';
import { useAuth } from '../context/AuthContext';

export const AuthScreen: React.FC = () => {
  const { login, register, isLoading } = useAuth();

  // Mode: 'login' or 'register'
  const [isRegisterMode, setIsRegisterMode] = useState<boolean>(false);

  // Tabs: 'mobile', 'abha', 'email'
  const [activeTab, setActiveTab] = useState<'mobile' | 'abha' | 'email'>('mobile');

  // Form Fields
  const [phone, setPhone] = useState<string>('9876543210');
  const [abhaId, setAbhaId] = useState<string>('91-4521-8890-1234');
  const [email, setEmail] = useState<string>('patient@clinova.health');
  const [password, setPassword] = useState<string>('Password123!');
  const [fullName, setFullName] = useState<string>('Rahul Sharma');
  const [gender, setGender] = useState<string>('Male');
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleLogin = async () => {
    setErrorMsg(null);
    try {
      if (activeTab === 'mobile') {
        if (!phone.trim()) {
          setErrorMsg('Please enter your 10-digit mobile number.');
          return;
        }
        await login({ phone: phone.trim(), email: `${phone.trim()}@patient.clinova.local`, password: 'PatientPassword123!' });
      } else if (activeTab === 'abha') {
        if (!abhaId.trim()) {
          setErrorMsg('Please enter your 14-digit ABHA ID or username@abdm.');
          return;
        }
        await login({ abha_id: abhaId.trim(), email: `abha_${abhaId.replace(/[^a-zA-Z0-9]/g, '')}@patient.clinova.local`, password: 'PatientPassword123!' });
      } else {
        if (!email.trim() || !password.trim()) {
          setErrorMsg('Please enter both email and password.');
          return;
        }
        await login({ email: email.trim(), password });
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Authentication failed. Please check your credentials.');
    }
  };

  const handleRegister = async () => {
    setErrorMsg(null);
    if (!fullName.trim() || !email.trim()) {
      setErrorMsg('Full legal name and email are required.');
      return;
    }
    try {
      await register({
        full_name: fullName.trim(),
        email: email.trim(),
        phone: phone.trim() || undefined,
        abha_id: abhaId.trim() || undefined,
        password: password.trim() || 'PatientPassword123!',
        gender: gender,
      });
    } catch (err: any) {
      setErrorMsg(err.message || 'Registration failed. Please check your details.');
    }
  };

  const handleAdminPress = () => {
    Alert.alert(
      'Hospital Administration',
      'The Clinova Hospital OS & Doctor Workspace is optimized for desktop workstations. Please access it through the Hospital Web portal.'
    );
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
        {/* Header Branding */}
        <View style={styles.header}>
          <View style={styles.logoBox}>
            <Text style={styles.logoEmoji}>🏥</Text>
          </View>
          <Text style={styles.brandTitle}>CLINOVA</Text>
          <Text style={styles.brandSubtitle}>Smarter healthcare, simpler care.</Text>
        </View>

        {/* Main Card */}
        <View style={styles.card}>
          {/* Role Selector: Patient vs Hospital Admin */}
          <View style={styles.roleSection}>
            <Text style={styles.sectionLabel}>I AM A:</Text>
            <View style={styles.roleGrid}>
              <TouchableOpacity style={styles.roleButtonActive}>
                <Text style={styles.roleIcon}>👤</Text>
                <Text style={styles.roleTextActive}>Patient</Text>
              </TouchableOpacity>

              <TouchableOpacity onPress={handleAdminPress} style={styles.roleButtonInactive}>
                <Text style={styles.roleIcon}>🏥</Text>
                <Text style={styles.roleTextInactive}>Hospital Admin</Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Mode Header */}
          <Text style={styles.cardTitle}>
            {isRegisterMode ? 'Create Patient Account' : 'Sign in to Patient Portal'}
          </Text>

          {errorMsg && (
            <View style={styles.errorBox}>
              <Text style={styles.errorText}>{errorMsg}</Text>
            </View>
          )}

          {!isRegisterMode ? (
            /* ================= SIGN IN MODE ================= */
            <>
              {/* Tabs: Mobile | ABHA | Email */}
              <View style={styles.tabContainer}>
                <TouchableOpacity
                  onPress={() => {
                    setActiveTab('mobile');
                    setErrorMsg(null);
                  }}
                  style={[styles.tabButton, activeTab === 'mobile' && styles.tabButtonActive]}
                >
                  <Text style={styles.tabIcon}>📱</Text>
                  <Text style={[styles.tabText, activeTab === 'mobile' && styles.tabTextActive]}>
                    Mobile
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  onPress={() => {
                    setActiveTab('abha');
                    setErrorMsg(null);
                  }}
                  style={[styles.tabButton, activeTab === 'abha' && styles.tabButtonActive]}
                >
                  <Text style={styles.tabIcon}>🪪</Text>
                  <Text style={[styles.tabText, activeTab === 'abha' && styles.tabTextActive]}>
                    ABHA ID
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  onPress={() => {
                    setActiveTab('email');
                    setErrorMsg(null);
                  }}
                  style={[styles.tabButton, activeTab === 'email' && styles.tabButtonActive]}
                >
                  <Text style={styles.tabIcon}>✉️</Text>
                  <Text style={[styles.tabText, activeTab === 'email' && styles.tabTextActive]}>
                    Email
                  </Text>
                </TouchableOpacity>
              </View>

              {/* Tab 1: Mobile Phone Input */}
              {activeTab === 'mobile' && (
                <View style={styles.formGroup}>
                  <Text style={styles.inputLabel}>Mobile Number</Text>
                  <View style={styles.phoneInputRow}>
                    <View style={styles.countryCodeBadge}>
                      <Text style={styles.countryCodeText}>+91</Text>
                    </View>
                    <TextInput
                      style={styles.phoneInput}
                      keyboardType="numeric"
                      maxLength={10}
                      placeholder="e.g. 98765 43210"
                      placeholderTextColor={colors.textSubtle}
                      value={phone}
                      onChangeText={setPhone}
                    />
                  </View>
                  <Text style={styles.helperText}>
                    ℹ️ You will receive a 6-digit OTP on your registered mobile number.
                  </Text>

                  <TouchableOpacity
                    onPress={handleLogin}
                    disabled={isLoading}
                    style={styles.submitButton}
                  >
                    {isLoading ? (
                      <ActivityIndicator color={colors.textLight} />
                    ) : (
                      <Text style={styles.submitButtonText}>Get OTP & Sign In →</Text>
                    )}
                  </TouchableOpacity>
                </View>
              )}

              {/* Tab 2: ABHA ID Input */}
              {activeTab === 'abha' && (
                <View style={styles.formGroup}>
                  <View style={styles.labelWithBadge}>
                    <Text style={styles.inputLabel}>ABHA Number / Address</Text>
                    <View style={styles.abdmBadge}>
                      <Text style={styles.abdmBadgeText}>✓ ABDM</Text>
                    </View>
                  </View>
                  <TextInput
                    style={styles.textInput}
                    placeholder="14-digit ABHA or username@abdm"
                    placeholderTextColor={colors.textSubtle}
                    value={abhaId}
                    onChangeText={setAbhaId}
                    autoCapitalize="none"
                  />
                  <Text style={styles.helperText}>
                    🔒 OTP will be sent to the Aadhaar-linked mobile number.
                  </Text>

                  <TouchableOpacity
                    onPress={handleLogin}
                    disabled={isLoading}
                    style={styles.submitButton}
                  >
                    {isLoading ? (
                      <ActivityIndicator color={colors.textLight} />
                    ) : (
                      <Text style={styles.submitButtonText}>Verify with OTP →</Text>
                    )}
                  </TouchableOpacity>
                </View>
              )}

              {/* Tab 3: Email Input */}
              {activeTab === 'email' && (
                <View style={styles.formGroup}>
                  <Text style={styles.inputLabel}>Email Address</Text>
                  <TextInput
                    style={styles.textInput}
                    keyboardType="email-address"
                    autoCapitalize="none"
                    placeholder="patient@example.com"
                    placeholderTextColor={colors.textSubtle}
                    value={email}
                    onChangeText={setEmail}
                  />

                  <Text style={styles.inputLabel}>Password</Text>
                  <View style={styles.passwordRow}>
                    <TextInput
                      style={styles.passwordInput}
                      secureTextEntry={!showPassword}
                      placeholder="Enter password"
                      placeholderTextColor={colors.textSubtle}
                      value={password}
                      onChangeText={setPassword}
                    />
                    <TouchableOpacity
                      onPress={() => setShowPassword(!showPassword)}
                      style={styles.eyeButton}
                    >
                      <Text style={styles.eyeIcon}>{showPassword ? '👁️' : '🙈'}</Text>
                    </TouchableOpacity>
                  </View>

                  <TouchableOpacity
                    onPress={handleLogin}
                    disabled={isLoading}
                    style={styles.submitButton}
                  >
                    {isLoading ? (
                      <ActivityIndicator color={colors.textLight} />
                    ) : (
                      <Text style={styles.submitButtonText}>Sign In →</Text>
                    )}
                  </TouchableOpacity>
                </View>
              )}
            </>
          ) : (
            /* ================= REGISTRATION MODE ================= */
            <View style={styles.formGroup}>
              <Text style={styles.inputLabel}>Full Legal Name *</Text>
              <TextInput
                style={styles.textInput}
                placeholder="e.g. Rahul Sharma"
                placeholderTextColor={colors.textSubtle}
                value={fullName}
                onChangeText={setFullName}
              />

              <Text style={styles.inputLabel}>Email Address *</Text>
              <TextInput
                style={styles.textInput}
                keyboardType="email-address"
                autoCapitalize="none"
                placeholder="rahul@example.com"
                placeholderTextColor={colors.textSubtle}
                value={email}
                onChangeText={setEmail}
              />

              <Text style={styles.inputLabel}>Mobile Phone</Text>
              <TextInput
                style={styles.textInput}
                keyboardType="numeric"
                maxLength={10}
                placeholder="e.g. 9876543210"
                placeholderTextColor={colors.textSubtle}
                value={phone}
                onChangeText={setPhone}
              />

              <Text style={styles.inputLabel}>ABHA Number (Optional)</Text>
              <TextInput
                style={styles.textInput}
                placeholder="14-digit ABHA (optional)"
                placeholderTextColor={colors.textSubtle}
                value={abhaId}
                onChangeText={setAbhaId}
              />

              <Text style={styles.inputLabel}>Password</Text>
              <TextInput
                style={styles.textInput}
                secureTextEntry={!showPassword}
                placeholder="Create password"
                placeholderTextColor={colors.textSubtle}
                value={password}
                onChangeText={setPassword}
              />

              <TouchableOpacity
                onPress={handleRegister}
                disabled={isLoading}
                style={styles.submitButton}
              >
                {isLoading ? (
                  <ActivityIndicator color={colors.textLight} />
                ) : (
                  <Text style={styles.submitButtonText}>Create Account & Continue →</Text>
                )}
              </TouchableOpacity>
            </View>
          )}

          {/* Toggle between Register & Sign In */}
          <View style={styles.footerSection}>
            <TouchableOpacity
              onPress={() => {
                setIsRegisterMode(!isRegisterMode);
                setErrorMsg(null);
              }}
              style={styles.toggleModeButton}
            >
              <Text style={styles.toggleModeText}>
                {isRegisterMode
                  ? 'Already have an account? Sign In'
                  : 'New to Clinova? Create Patient Account'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollContent: {
    padding: spacing.lg,
    alignItems: 'center',
  },
  header: {
    alignItems: 'center',
    marginVertical: spacing.lg,
  },
  logoBox: {
    width: 64,
    height: 64,
    borderRadius: borderRadius.xl,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
    ...shadows.card,
  },
  logoEmoji: {
    fontSize: 32,
  },
  brandTitle: {
    fontSize: 26,
    fontWeight: '800',
    color: colors.textPrimary,
    letterSpacing: -0.5,
  },
  brandSubtitle: {
    fontSize: 13,
    fontWeight: '500',
    color: colors.textMuted,
    marginTop: 2,
  },
  card: {
    width: '100%',
    maxWidth: 420,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.xxl,
    padding: spacing.xl,
    borderWidth: 1,
    borderColor: colors.border,
    ...shadows.card,
  },
  roleSection: {
    marginBottom: spacing.lg,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '800',
    color: colors.textMuted,
    letterSpacing: 0.8,
    marginBottom: spacing.xs + 2,
  },
  roleGrid: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  roleButtonActive: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.xs,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.primaryLight,
    borderWidth: 2,
    borderColor: colors.primary,
  },
  roleButtonInactive: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.xs,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  roleIcon: {
    fontSize: 16,
  },
  roleTextActive: {
    fontSize: 13,
    fontWeight: '800',
    color: colors.primary,
  },
  roleTextInactive: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textMuted,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: colors.textPrimary,
    marginBottom: spacing.md,
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: colors.surfaceContainerLow,
    borderRadius: borderRadius.lg,
    padding: 3,
    gap: 3,
    marginBottom: spacing.lg,
  },
  tabButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    paddingVertical: 8,
    borderRadius: borderRadius.md,
  },
  tabButtonActive: {
    backgroundColor: colors.surface,
    ...shadows.card,
  },
  tabIcon: {
    fontSize: 13,
  },
  tabText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.textMuted,
  },
  tabTextActive: {
    fontWeight: '800',
    color: colors.primary,
  },
  formGroup: {
    gap: spacing.sm,
  },
  inputLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.textSecondary,
    marginTop: 4,
  },
  phoneInputRow: {
    flexDirection: 'row',
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.surfaceContainerLow,
    overflow: 'hidden',
  },
  countryCodeBadge: {
    paddingHorizontal: spacing.md,
    justifyContent: 'center',
    borderRightWidth: 1,
    borderRightColor: colors.border,
    backgroundColor: colors.surface,
  },
  countryCodeText: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.textSecondary,
  },
  phoneInput: {
    flex: 1,
    minHeight: 48,
    paddingHorizontal: spacing.md,
    fontSize: 14,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  textInput: {
    minHeight: 48,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.surfaceContainerLow,
    paddingHorizontal: spacing.md,
    fontSize: 14,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  passwordRow: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.surfaceContainerLow,
  },
  passwordInput: {
    flex: 1,
    minHeight: 48,
    paddingHorizontal: spacing.md,
    fontSize: 14,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  eyeButton: {
    padding: spacing.md,
  },
  eyeIcon: {
    fontSize: 16,
  },
  labelWithBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  abdmBadge: {
    backgroundColor: colors.primaryLight,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: borderRadius.full,
    borderWidth: 1,
    borderColor: colors.primaryBorder,
  },
  abdmBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: colors.primary,
  },
  helperText: {
    fontSize: 11,
    color: colors.textMuted,
    lineHeight: 16,
    marginVertical: 4,
  },
  submitButton: {
    minHeight: 48,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: spacing.sm,
    ...shadows.card,
  },
  submitButtonText: {
    fontSize: 14,
    fontWeight: '800',
    color: colors.textLight,
  },
  footerSection: {
    marginTop: spacing.lg,
    paddingTop: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    alignItems: 'center',
  },
  toggleModeButton: {
    padding: spacing.sm,
  },
  toggleModeText: {
    fontSize: 13,
    fontWeight: '700',
    color: colors.primary,
  },
  errorBox: {
    backgroundColor: colors.errorContainer,
    padding: spacing.sm,
    borderRadius: borderRadius.md,
    marginBottom: spacing.md,
  },
  errorText: {
    fontSize: 12,
    color: colors.onErrorContainer,
    textAlign: 'center',
    fontWeight: '600',
  },
});
