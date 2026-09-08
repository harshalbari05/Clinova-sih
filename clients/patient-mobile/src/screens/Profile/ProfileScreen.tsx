import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { NavigationProp } from '../../navigation/types';
import { usePatient } from '../../context/PatientContext';
import { patientApi } from '../../api';
import colors from '../../theme/colors';
import { borderRadius, spacing } from '../../theme/spacing';
import Header from '../../components/Header';
import Card from '../../components/Card';
import Input from '../../components/Input';
import Button from '../../components/Button';

export const ProfileScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp<'Profile'>>();
  const { patient, user, refreshProfile, logout } = usePatient();

  const [fullName, setFullName] = useState(patient?.full_name || '');
  const [phone, setPhone] = useState(patient?.phone || '');
  const [dob, setDob] = useState(patient?.date_of_birth || patient?.dob || '');
  const [gender, setGender] = useState(patient?.gender || 'other');
  const [abhaId, setAbhaId] = useState(patient?.abha_id || '');
  const [address, setAddress] = useState(patient?.address || '');
  const [emergencyContact, setEmergencyContact] = useState(patient?.emergency_contact || '');

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleUpdateProfile = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(false);

      await patientApi.updateProfile({
        full_name: fullName.trim(),
        phone: phone.trim() || undefined,
        date_of_birth: dob.trim() || undefined,
        gender: gender || undefined,
        abha_id: abhaId.trim() || undefined,
        address: address.trim() || undefined,
        emergency_contact: emergencyContact.trim() || undefined,
      });

      await refreshProfile();
      setSuccess(true);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to update profile.');
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = () => {
    Alert.alert('Sign Out', 'Are you sure you want to sign out of your Clinova account?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Sign Out',
        style: 'destructive',
        onPress: async () => {
          await logout();
        },
      },
    ]);
  };

  return (
    <View style={styles.container}>
      <Header title="Patient Profile" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
        {/* User Identity Banner */}
        <Card elevated style={styles.userBanner}>
          <View style={styles.avatarCircle}>
            <Text style={styles.avatarText}>
              {(patient?.full_name || 'P').charAt(0).toUpperCase()}
            </Text>
          </View>
          <View style={styles.userInfo}>
            <Text style={styles.userName}>{patient?.full_name || 'Patient Profile'}</Text>
            <Text style={styles.userEmail}>{user?.email || patient?.phone || 'Clinova Patient'}</Text>
            {patient?.abha_id && (
              <View style={styles.abhaBadge}>
                <Ionicons name="card-outline" size={12} color={colors.primary} />
                <Text style={styles.abhaText}>ABHA: {patient.abha_id}</Text>
              </View>
            )}
          </View>
        </Card>

        {/* Profile Edit Form */}
        <Card style={styles.formCard}>
          <Text style={styles.sectionHeader}>Personal & Demographic Information</Text>

          {error && (
            <View style={styles.errorBox}>
              <Text style={styles.errorBoxText}>{error}</Text>
            </View>
          )}

          {success && (
            <View style={styles.successBox}>
              <Text style={styles.successBoxText}>Profile updated successfully!</Text>
            </View>
          )}

          <Input
            label="Full Name"
            value={fullName}
            onChangeText={(t) => {
              setFullName(t);
              setSuccess(false);
            }}
          />

          <Input
            label="Phone Number"
            value={phone}
            onChangeText={(t) => {
              setPhone(t);
              setSuccess(false);
            }}
            keyboardType="phone-pad"
          />

          <Input
            label="Date of Birth (YYYY-MM-DD)"
            value={dob}
            onChangeText={(t) => {
              setDob(t);
              setSuccess(false);
            }}
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
                onPress={() => {
                  setGender(g);
                  setSuccess(false);
                }}
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
            label="ABHA ID"
            value={abhaId}
            onChangeText={(t) => {
              setAbhaId(t);
              setSuccess(false);
            }}
            helperText="Ayushman Bharat Health Account ID"
          />

          <Input
            label="Residential Address"
            value={address}
            onChangeText={(t) => {
              setAddress(t);
              setSuccess(false);
            }}
            multiline
            numberOfLines={2}
          />

          <Input
            label="Emergency Contact"
            value={emergencyContact}
            onChangeText={(t) => {
              setEmergencyContact(t);
              setSuccess(false);
            }}
            keyboardType="phone-pad"
          />

          <Button
            title="Save Changes"
            onPress={handleUpdateProfile}
            loading={saving}
            style={{ marginTop: spacing.sm }}
          />
        </Card>

        {/* Account Actions */}
        <Card style={styles.accountCard}>
          <Text style={styles.sectionHeader}>Security & Account</Text>

          <TouchableOpacity
            style={styles.actionRow}
            activeOpacity={0.7}
            onPress={handleLogout}
          >
            <View style={styles.actionLeft}>
              <Ionicons name="log-out-outline" size={20} color={colors.error} />
              <Text style={styles.logoutText}>Sign Out of Clinova</Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color={colors.error} />
          </TouchableOpacity>
        </Card>

        <Text style={styles.versionText}>
          Clinova Patient Mobile v1.0.0 • Hardware Token Encrypted
        </Text>
      </ScrollView>
    </View>
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
  userBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  avatarCircle: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  avatarText: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.onPrimary,
  },
  userInfo: {
    flex: 1,
  },
  userName: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.onSurface,
  },
  userEmail: {
    fontSize: 13,
    color: colors.textSecondary,
    marginTop: 2,
  },
  abhaBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceContainer,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: borderRadius.sm,
    alignSelf: 'flex-start',
    marginTop: 6,
  },
  abhaText: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.primary,
    marginLeft: 4,
  },
  formCard: {
    marginBottom: spacing.md,
    padding: spacing.md,
  },
  sectionHeader: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.onSurface,
    marginBottom: spacing.md,
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
  },
  successBox: {
    backgroundColor: '#DCFCE7',
    padding: spacing.md,
    borderRadius: borderRadius.sm,
    marginBottom: spacing.md,
  },
  successBoxText: {
    color: '#15803D',
    fontSize: 13,
    fontWeight: '600',
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
  accountCard: {
    marginBottom: spacing.lg,
    padding: spacing.md,
  },
  actionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: spacing.sm,
  },
  actionLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  logoutText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.error,
    marginLeft: spacing.sm,
  },
  versionText: {
    fontSize: 11,
    color: colors.textMuted,
    textAlign: 'center',
    marginTop: spacing.sm,
  },
});

export default ProfileScreen;
