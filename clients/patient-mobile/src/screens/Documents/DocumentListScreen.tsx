import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { NavigationProp, ScreenRouteProp } from '../../navigation/types';
import { documentApi } from '../../api';
import { MedicalDocument } from '../../types';
import colors from '../../theme/colors';
import { borderRadius, spacing } from '../../theme/spacing';
import Header from '../../components/Header';
import Card from '../../components/Card';
import Badge from '../../components/Badge';
import EmptyState from '../../components/EmptyState';

export const DocumentListScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp<'DocumentList'>>();
  const route = useRoute<ScreenRouteProp<'DocumentList'>>();
  const consultationId = route.params?.consultationId;

  const [documents, setDocuments] = useState<MedicalDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchDocuments = useCallback(async () => {
    try {
      const res = await documentApi.listDocuments(consultationId);
      setDocuments(res.items || []);
    } catch {
      // Ignore network errors on refresh
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [consultationId]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchDocuments();
  };

  const getDocTypeIcon = (type: string): keyof typeof Ionicons.glyphMap => {
    switch (type) {
      case 'prescription':
        return 'medical-outline';
      case 'lab_report':
        return 'flask-outline';
      case 'discharge_summary':
        return 'clipboard-outline';
      case 'radiology_scan':
        return 'scan-outline';
      default:
        return 'document-text-outline';
    }
  };

  return (
    <View style={styles.container}>
      <Header
        title="Medical Documents"
        onBack={() => navigation.goBack()}
        rightAction={
          <TouchableOpacity
            onPress={() => navigation.navigate('DocumentUpload', { consultationId })}
            style={styles.addBtn}
          >
            <Ionicons name="add" size={24} color={colors.primary} />
          </TouchableOpacity>
        }
      />

      {loading ? (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Loading documents...</Text>
        </View>
      ) : documents.length === 0 ? (
        <EmptyState
          icon="folder-open-outline"
          title="No Medical Documents"
          description="Upload prescriptions, lab reports, or discharge summaries to extract clinical facts."
          actionTitle="Upload Document"
          onAction={() => navigation.navigate('DocumentUpload', { consultationId })}
        />
      ) : (
        <FlatList
          data={documents}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[colors.primary]} />
          }
          renderItem={({ item }) => {
            const isProcessed = item.ocr_status === 'completed' || item.processing_status === 'processed';
            return (
              <TouchableOpacity
                activeOpacity={0.8}
                onPress={() => navigation.navigate('DocumentExtraction', { documentId: item.id })}
              >
                <Card style={styles.docCard}>
                  <View style={styles.docIconCircle}>
                    <Ionicons name={getDocTypeIcon(item.document_type)} size={24} color={colors.primary} />
                  </View>

                  <View style={styles.docDetails}>
                    <Text style={styles.docFilename} numberOfLines={1}>
                      {item.filename || item.file_name || item.original_filename || 'Medical Document'}
                    </Text>

                    <Text style={styles.docType}>
                      {item.document_type.replace('_', ' ').toUpperCase()}
                    </Text>

                    <Text style={styles.docDate}>
                      Uploaded: {new Date(item.created_at).toLocaleDateString()}
                    </Text>
                  </View>

                  <View style={styles.docStatusCol}>
                    <Badge
                      label={isProcessed ? 'OCR Ready' : 'Processing'}
                      variant={isProcessed ? 'verified' : 'yellow'}
                    />
                    <Ionicons
                      name="chevron-forward"
                      size={18}
                      color={colors.textMuted}
                      style={{ marginTop: 8 }}
                    />
                  </View>
                </Card>
              </TouchableOpacity>
            );
          }}
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
  addBtn: {
    padding: spacing.xs,
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
  listContent: {
    padding: spacing.md,
  },
  docCard: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
    padding: spacing.md,
  },
  docIconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.surfaceContainer,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  docDetails: {
    flex: 1,
  },
  docFilename: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.onSurface,
  },
  docType: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.primary,
    marginTop: 2,
  },
  docDate: {
    fontSize: 11,
    color: colors.textSecondary,
    marginTop: 2,
  },
  docStatusCol: {
    alignItems: 'flex-end',
    marginLeft: spacing.sm,
  },
});

export default DocumentListScreen;
