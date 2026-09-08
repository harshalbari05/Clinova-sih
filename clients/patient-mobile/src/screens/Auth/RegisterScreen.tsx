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
import { borderRadius, spacing } from '../../theme/spacing';
import Input from '../../components/Input';
import Button from '../../components/Button';
import Card from '../../components/Card';
import Header from '../../components/Header';

export const RegisterScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp<'Register'>>();
  const { login } = usePatient();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [dob, setDob] = useState('');
  const [gender, setGender] = useState('other');
  const [abhaId, setAbhaId] = useState('');
  const [emergencyContact, setEmergencyContact] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRegister = async () => {
    if (!fullName.trim()) {
      setError('Please enter your full name.');
      return;
    }
    if (!email.trim() && !phone.trim()) {
      setError('Please provide at least an email address or phone number.');
      return;
    }
    if (!password || password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      await authApi.register({
        full_name: fullName.trim(),
        email: email.trim() || undefined,
        phone: phone.trim() || undefined,
        password,
        date_of_birth: dob.trim() || undefined,
        gender: gender || undefined,
        abha_id: abhaId.trim() || undefined,
        emergency_contact: emergencyContact.trim() || undefined,
      });

      // Automatically log the patient in after successful registration
      const loginRes = await authApi.login({
        identifier: email.trim() || phone.trim(),
        password,
      });

      await login(loginRes);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Registration failed. Please check the provided information.';
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
      <Header title="Patient Registration" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
        <Card elevated style={styles.card}>
          <Text style={styles.cardTitle}>Create Patient Account</Text>
          <Text style={styles.cardSubtitle}>
            Register your profile to begin clinical intake and preserve medical records.
          </Text>

          {error && (
            <View style={styles.errorBox}>
              <Text style={styles.errorBoxText}>{error}</Text>
            </View>
          )}

          <Input
            label="Full Name *"
            placeholder="e.g. Rahul Sharma"
            value={fullName}
            onChangeText={(t) => {
              setFullName(t);
              setError(null);
            }}
          />

          <Input
            label="Email Address"
            placeholder="e.g. rahul@example.com"
            value={email}
            onChangeText={(t) => {
              setEmail(t);
              setError(null);
            }}
            keyboardType="email-address"
            autoCapitalize="none"
          />

          <Input
            label="Phone Number"
            placeholder="e.g. 9876543210"
            value={phone}
            onChangeText={(t) => {
              setPhone(t);
              setError(null);
            }}
            keyboardType="phone-pad"
          />

          <Input
            label="Password (min 8 characters) *"
            placeholder="Create a strong password"
            value={password}
            onChangeText={(t) => {
              setPassword(t);
              setError(null);
            }}
            secureTextEntry
          />

          <Input
            label="Date of Birth (YYYY-MM-DD)"
            placeholder="e.g. 1990-05-15"
            value={dob}
            onChangeText={setDob}
          />

          {/* Gender Selector */}
          <Text style={styles.fieldLabel}>Gender</Text>
          <View style={styles.genderRow}>
            {['male', 'female', 'other'].map((g) => (
              <TouchableOpacity
                key={g}
                style={[
                  styles.genderOption,
                  gender === g && styles.genderOptionSelected,
                ]}
                onPress={() => setGender(g)}
              >
                <Text
                  style={[
                    styles.genderOptionText,
                    gender === g && styles.genderOptionTextSelected,
                  ]}
                >
                  {g.charAt(0).toUpperCase() + g.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <Input
            label="ABHA ID / Address (Optional)"
            placeholder="e.g. 12-3456-7890-1234 or name@abdm"
            value={abhaId}
            onChangeText={setAbhaId}
            helperText="Ayushman Bharat Health Account ID (if available)"
          />

          <Input
            label="Emergency Contact Phone (Optional)"
            placeholder="e.g. 9876500000"
            value={emergencyContact}
            onChangeText={setEmergencyContact}
            keyboardType="phone-pad"
          />

          <Button
            title="Create Account & Sign In"
            onPress={handleRegister}
            loading={loading}
            style={styles.registerBtn}
          />

          <View style={styles.loginRow}>
            <Text style={styles.loginText}>Already registered? </Text>
            <TouchableOpacity onPress={() => navigation.navigate('Login')}>
              <Text style={styles.loginLink}>Sign In</Text>
            </TouchableOpacity>
          </View>
        </Card>
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
    padding: spacing.md,
    paddingBottom: spacing.xxl,
  },
  card: {
    padding: spacing.lg,
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
  fieldLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.onSurfaceVariant,
    marginBottom: spacing.xs,
  },
  genderRow: {
    flexDirection: 'row',
    marginBottom: spacing.md,
  },
  genderOption: {
    flex: 1,
    height: 40,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.xs,
    backgroundColor: colors.surfaceContainerLowest,
  },
  genderOptionSelected: {
    borderColor: colors.primary,
    backgroundColor: colors.secondaryContainer,
  },
  genderOptionText: {
    fontSize: 13,
    fontWeight: '500',
    color: colors.onSurface,
  },
  genderOptionTextSelected: {
    color: colors.onSecondaryContainer,
    fontWeight: '700',
  },
  registerBtn: {
    marginTop: spacing.md,
  },
  loginRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: spacing.lg,
  },
  loginText: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  loginLink: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.primary,
  },
});

export default RegisterScreen;
