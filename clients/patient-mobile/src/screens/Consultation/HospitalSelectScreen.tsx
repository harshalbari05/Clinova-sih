import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { NavigationProp } from '../../navigation/types';
import { usePatient } from '../../context/PatientContext';
import { hospitalApi } from '../../api';
import { Hospital } from '../../types';
import colors from '../../theme/colors';
import { borderRadius, spacing } from '../../theme/spacing';
import Header from '../../components/Header';
import Card from '../../components/Card';
import Input from '../../components/Input';
import StepIndicator from '../../components/StepIndicator';

export const HospitalSelectScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp<'HospitalSelect'>>();
  const { setSelectedHospital } = usePatient();

  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setError(null);
        const list = await hospitalApi.listHospitals();
        setHospitals(list || []);
      } catch (err: any) {
        setError('Unable to load hospital directory. Please check network connection.');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const filteredHospitals = hospitals.filter((h) => {
    const q = search.toLowerCase();
    return (
      h.name.toLowerCase().includes(q) ||
      (h.city && h.city.toLowerCase().includes(q)) ||
      (h.state && h.state.toLowerCase().includes(q))
    );
  });

  const handleSelectHospital = async (hospital: Hospital) => {
    await setSelectedHospital(hospital);
    navigation.navigate('Consent', { hospitalId: hospital.id });
  };

  return (
    <View style={styles.container}>
      <Header title="Select Hospital" onBack={() => navigation.goBack()} />
      <StepIndicator currentStep={1} />

      <View style={styles.searchContainer}>
        <Input
          placeholder="Search by hospital name, city, or state..."
          value={search}
          onChangeText={setSearch}
          containerStyle={{ marginBottom: 0 }}
        />
      </View>

      {loading ? (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Loading hospital facilities...</Text>
        </View>
      ) : error ? (
        <View style={styles.centerContainer}>
          <Ionicons name="alert-circle-outline" size={40} color={colors.error} />
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : filteredHospitals.length === 0 ? (
        <View style={styles.centerContainer}>
          <Ionicons name="business-outline" size={40} color={colors.textMuted} />
          <Text style={styles.emptyTitle}>No Hospitals Found</Text>
          <Text style={styles.emptySubtitle}>
            Try changing your search query or check back later.
          </Text>
        </View>
      ) : (
        <FlatList
          data={filteredHospitals}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContent}
          renderItem={({ item }) => (
            <TouchableOpacity
              activeOpacity={0.8}
              onPress={() => handleSelectHospital(item)}
            >
              <Card style={styles.hospitalCard}>
                <View style={styles.hospitalIconCircle}>
                  <Ionicons name="business" size={24} color={colors.primary} />
                </View>
                <View style={styles.hospitalInfo}>
                  <Text style={styles.hospitalName}>{item.name}</Text>
                  <View style={styles.locationRow}>
                    <Ionicons name="location-outline" size={14} color={colors.textSecondary} />
                    <Text style={styles.locationText}>
                      {[item.city, item.state].filter(Boolean).join(', ') || 'Facility Active'}
                    </Text>
                  </View>
                </View>
                <Ionicons name="chevron-forward" size={20} color={colors.primary} />
              </Card>
            </TouchableOpacity>
          )}
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.surface,
  },
  searchContainer: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    backgroundColor: colors.surfaceContainerLowest,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  listContent: {
    padding: spacing.md,
  },
  centerContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
  },
  loadingText: {
    fontSize: 14,
    color: colors.textSecondary,
    marginTop: spacing.sm,
  },
  errorText: {
    fontSize: 14,
    color: colors.error,
    marginTop: spacing.sm,
    textAlign: 'center',
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.onSurface,
    marginTop: spacing.sm,
  },
  emptySubtitle: {
    fontSize: 13,
    color: colors.textSecondary,
    marginTop: 4,
    textAlign: 'center',
  },
  hospitalCard: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
    padding: spacing.md,
  },
  hospitalIconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.secondaryContainer,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  hospitalInfo: {
    flex: 1,
  },
  hospitalName: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.onSurface,
  },
  locationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 2,
  },
  locationText: {
    fontSize: 12,
    color: colors.textSecondary,
    marginLeft: 3,
  },
});

export default HospitalSelectScreen;
