import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NavigationProp } from '../../navigation/types';
import { usePatient } from '../../context/PatientContext';
import { authApi } from '../../api';
import colors from '../../theme/colors';
import { borderRadius, spacing, shadows } from '../../theme/spacing';
import Input from '../../components/Input';
import Button from '../../components/Button';
import Card from '../../components/Card';

export const LoginScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp<'Login'>>();
  const { login } = usePatient();

  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async () => {
    if (!identifier.trim()) {
      setError('Please enter your email, phone number, or ABHA ID.');
      return;
    }
    if (!password) {
      setError('Please enter your password.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await authApi.login({
        identifier: identifier.trim(),
        password,
      });

      if (res.account_type !== 'patient') {
        setError('This app is for patients only. Please use the Hospital portal for staff logins.');
        return;
      }

      await login(res);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Invalid login credentials. Please verify and try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      style={styles.container}
    >
      <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
        {/* Header Branding */}
        <View style={styles.header}>
          <View style={styles.logoBadge}>
            <Text style={styles.logoBadgeText}>+</Text>
          </View>
          <Text style={styles.title}>Clinova</Text>
          <Text style={styles.subtitle}>Patient Clinical Intake & Medical History</Text>
        </View>

        {/* Login Card */}
        <Card elevated style={styles.card}>
          <Text style={styles.cardTitle}>Patient Sign In</Text>
          <Text style={styles.cardSubtitle}>
            Access your intake consultations, medical records, and clinical summaries.
          </Text>

          {error && (
            <View style={styles.errorBox}>
              <Text style={styles.errorBoxText}>{error}</Text>
            </View>
          )}

          <Input
            label="Email, Phone, or ABHA ID"
            placeholder="e.g. patient@example.com or 9876543210"
            value={identifier}
            onChangeText={(t) => {
              setIdentifier(t);
              setError(null);
            }}
            autoCapitalize="none"
            keyboardType="email-address"
          />

          <Input
            label="Password"
            placeholder="Enter your password"
            value={password}
            onChangeText={(t) => {
              setPassword(t);
              setError(null);
            }}
            secureTextEntry
          />

          <Button
            title="Sign In"
            onPress={handleLogin}
            loading={loading}
            style={styles.loginBtn}
          />

          <View style={styles.registerRow}>
            <Text style={styles.registerText}>Don't have an account? </Text>
            <TouchableOpacity onPress={() => navigation.navigate('Register')}>
              <Text style={styles.registerLink}>Register</Text>
            </TouchableOpacity>
          </View>
        </Card>

        <Text style={styles.footerNote}>
          Clinova SIH 2026 • AI-Powered Clinical Intake Platform
        </Text>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.surface,
  },
  scrollContent: {
    flexGrow: 1,
    padding: spacing.lg,
    justifyContent: 'center',
  },
  header: {
    alignItems: 'center',
    marginBottom: spacing.xl,
  },
  logoBadge: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
    ...shadows.subtle,
  },
  logoBadgeText: {
    color: colors.onPrimary,
    fontSize: 32,
    fontWeight: '700',
    lineHeight: 36,
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    color: colors.primary,
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.textSecondary,
    textAlign: 'center',
    marginTop: 4,
  },
  card: {
    padding: spacing.lg,
    marginBottom: spacing.xl,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.onSurface,
  },
  cardSubtitle: {
    fontSize: 13,
    color: colors.textSecondary,
    marginTop: 4,
    marginBottom: spacing.lg,
    lineHeight: 18,
  },
  loginBtn: {
    marginTop: spacing.sm,
  },
  errorBox: {
    backgroundColor: colors.errorContainer,
    padding: spacing.md,
    borderRadius: borderRadius.sm,
    marginBottom: spacing.md,
  },
  errorBoxText: {
    color: colors.error,
    fontSize: 13,
    fontWeight: '500',
  },
  registerRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: spacing.lg,
  },
  registerText: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  registerLink: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.primary,
  },
  footerNote: {
    textAlign: 'center',
    fontSize: 12,
    color: colors.textMuted,
  },
});

export default LoginScreen;
