/**
 * Mobile Camera Document Scanner Component
 * Viewfinder with alignment guide, capture, preview, retake, and confirmation.
 * Matches clinova_medical_document_scanning_ocr design.
 */
import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  Modal,
  StyleSheet,
  TouchableOpacity,
  Image,
  ActivityIndicator,
} from 'react-native';
import { CameraView, CameraType, useCameraPermissions } from 'expo-camera';
import * as ImagePicker from 'expo-image-picker';
import { colors, typography, spacing, borderRadius } from '../../constants/theme';

interface CameraScannerProps {
  visible: boolean;
  onClose: () => void;
  onCaptureConfirmed: (imageUri: string, mimeType: string, filename: string) => void;
}

export const CameraScanner: React.FC<CameraScannerProps> = ({
  visible,
  onClose,
  onCaptureConfirmed,
}) => {
  const [permission, requestPermission] = useCameraPermissions();
  const [facing, setFacing] = useState<CameraType>('back');
  const [capturedUri, setCapturedUri] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const cameraRef = useRef<any>(null);

  const handleTakePicture = async () => {
    if (!cameraRef.current) return;
    try {
      setIsProcessing(true);
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.85,
        skipProcessing: false,
      });
      if (photo?.uri) {
        setCapturedUri(photo.uri);
      }
    } catch {
      // Camera capture error handled gracefully
    } finally {
      setIsProcessing(false);
    }
  };

  const handlePickFromGallery = async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        allowsEditing: true,
        quality: 0.85,
      });

      if (!result.canceled && result.assets[0]?.uri) {
        setCapturedUri(result.assets[0].uri);
      }
    } catch {
      // Photo library pick handled safely
    }
  };

  const handleRetake = () => {
    setCapturedUri(null);
  };

  const handleConfirm = () => {
    if (!capturedUri) return;
    const filename = capturedUri.split('/').pop() || 'medical_report.jpg';
    const mimeType = filename.endsWith('.png') ? 'image/png' : 'image/jpeg';
    onCaptureConfirmed(capturedUri, mimeType, filename);
    setCapturedUri(null);
    onClose();
  };

  const toggleFacing = () => {
    setFacing((current) => (current === 'back' ? 'front' : 'back'));
  };

  if (!visible) return null;

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      <View style={styles.container}>
        {/* Permission Denied View */}
        {!permission?.granted ? (
          <View style={styles.permissionContainer}>
            <Text style={styles.permissionEmoji}>📷</Text>
            <Text style={styles.permissionTitle}>Camera Access Required</Text>
            <Text style={styles.permissionText}>
              Clinova needs camera permission to scan and extract medical reports and prescriptions.
            </Text>

            <TouchableOpacity onPress={requestPermission} style={styles.grantButton}>
              <Text style={styles.grantButtonText}>Allow Camera Access</Text>
            </TouchableOpacity>

            <TouchableOpacity onPress={handlePickFromGallery} style={styles.galleryFallbackButton}>
              <Text style={styles.galleryFallbackText}>Select from Photos Instead</Text>
            </TouchableOpacity>

            <TouchableOpacity onPress={onClose} style={styles.cancelButton}>
              <Text style={styles.cancelText}>Cancel</Text>
            </TouchableOpacity>
          </View>
        ) : capturedUri ? (
          /* Captured Preview & Confirmation Screen */
          <View style={styles.previewContainer}>
            <View style={styles.previewHeader}>
              <Text style={styles.previewTitle}>Review Captured Document</Text>
              <Text style={styles.previewSubtitle}>Make sure text is readable and flat</Text>
            </View>

            <View style={styles.imageWrapper}>
              <Image source={{ uri: capturedUri }} style={styles.previewImage} resizeMode="contain" />
            </View>

            <View style={styles.previewActions}>
              <TouchableOpacity onPress={handleRetake} style={styles.retakeButton}>
                <Text style={styles.retakeText}>Retake Photo</Text>
              </TouchableOpacity>

              <TouchableOpacity onPress={handleConfirm} style={styles.confirmButton}>
                <Text style={styles.confirmText}>Confirm & Process OCR</Text>
              </TouchableOpacity>
            </View>
          </View>
        ) : (
          /* Live Camera Viewfinder */
          <View style={styles.cameraWrapper}>
            <CameraView ref={cameraRef} style={styles.camera} facing={facing}>
              {/* Top Viewfinder Controls */}
              <View style={styles.topControls}>
                <TouchableOpacity onPress={onClose} style={styles.roundButton}>
                  <Text style={styles.roundButtonText}>✕</Text>
                </TouchableOpacity>

                <View style={styles.scanBadge}>
                  <Text style={styles.scanBadgeText}>Document Scan</Text>
                </View>

                <TouchableOpacity onPress={toggleFacing} style={styles.roundButton}>
                  <Text style={styles.roundButtonText}>🔄</Text>
                </TouchableOpacity>
              </View>

              {/* Viewfinder Alignment Guide Rectangle */}
              <View style={styles.guideContainer}>
                <View style={styles.documentFrame}>
                  {/* Corner marks */}
                  <View style={[styles.corner, styles.cornerTL]} />
                  <View style={[styles.corner, styles.cornerTR]} />
                  <View style={[styles.corner, styles.cornerBL]} />
                  <View style={[styles.corner, styles.cornerBR]} />
                  <Text style={styles.guideText}>Align prescription or lab report inside frame</Text>
                </View>
              </View>

              {/* Bottom Capture Controls */}
              <View style={styles.bottomControls}>
                <TouchableOpacity onPress={handlePickFromGallery} style={styles.galleryButton}>
                  <Text style={styles.galleryIcon}>🖼️</Text>
                  <Text style={styles.galleryLabel}>Photos</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  onPress={handleTakePicture}
                  disabled={isProcessing}
                  style={styles.shutterButton}
                >
                  {isProcessing ? (
                    <ActivityIndicator size="large" color={colors.primary} />
                  ) : (
                    <View style={styles.shutterInner} />
                  )}
                </TouchableOpacity>

                <View style={styles.dummySpacer} />
              </View>
            </CameraView>
          </View>
        )}
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  permissionContainer: {
    flex: 1,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
  },
  permissionEmoji: {
    fontSize: 56,
    marginBottom: spacing.md,
  },
  permissionTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: colors.textPrimary,
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
  permissionText: {
    fontSize: 14,
    color: colors.textMuted,
    textAlign: 'center',
    marginBottom: spacing.xl,
    lineHeight: 20,
  },
  grantButton: {
    width: '100%',
    minHeight: 48,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
  },
  grantButtonText: {
    color: colors.textLight,
    fontSize: 15,
    fontWeight: '700',
  },
  galleryFallbackButton: {
    width: '100%',
    minHeight: 48,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.surfaceContainerLow,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
  },
  galleryFallbackText: {
    color: colors.primary,
    fontSize: 14,
    fontWeight: '700',
  },
  cancelButton: {
    padding: spacing.md,
  },
  cancelText: {
    color: colors.textMuted,
    fontSize: 14,
  },
  cameraWrapper: {
    flex: 1,
  },
  camera: {
    flex: 1,
    justifyContent: 'space-between',
  },
  topControls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingTop: 48,
  },
  roundButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(0,0,0,0.5)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  roundButtonText: {
    color: colors.textLight,
    fontSize: 16,
    fontWeight: '700',
  },
  scanBadge: {
    backgroundColor: 'rgba(0, 104, 95, 0.85)',
    paddingHorizontal: spacing.md,
    paddingVertical: 6,
    borderRadius: borderRadius.full,
  },
  scanBadgeText: {
    color: colors.textLight,
    fontSize: 12,
    fontWeight: '700',
  },
  guideContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: spacing.xl,
  },
  documentFrame: {
    width: '100%',
    height: '75%',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.4)',
    borderRadius: borderRadius.lg,
    position: 'relative',
    alignItems: 'center',
    justifyContent: 'center',
  },
  corner: {
    position: 'absolute',
    width: 24,
    height: 24,
    borderColor: colors.emerald,
  },
  cornerTL: { top: -2, left: -2, borderTopWidth: 3, borderLeftWidth: 3 },
  cornerTR: { top: -2, right: -2, borderTopWidth: 3, borderRightWidth: 3 },
  cornerBL: { bottom: -2, left: -2, borderBottomWidth: 3, borderLeftWidth: 3 },
  cornerBR: { bottom: -2, right: -2, borderBottomWidth: 3, borderRightWidth: 3 },
  guideText: {
    color: 'rgba(255,255,255,0.85)',
    fontSize: 13,
    fontWeight: '600',
    backgroundColor: 'rgba(0,0,0,0.5)',
    paddingHorizontal: spacing.md,
    paddingVertical: 6,
    borderRadius: borderRadius.md,
  },
  bottomControls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.xxl,
    paddingBottom: 40,
  },
  galleryButton: {
    alignItems: 'center',
  },
  galleryIcon: {
    fontSize: 24,
  },
  galleryLabel: {
    color: colors.textLight,
    fontSize: 11,
    fontWeight: '600',
    marginTop: 2,
  },
  shutterButton: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: 'rgba(255,255,255,0.3)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  shutterInner: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.surface,
  },
  dummySpacer: {
    width: 36,
  },
  previewContainer: {
    flex: 1,
    backgroundColor: colors.surface,
    paddingTop: 48,
    justifyContent: 'space-between',
  },
  previewHeader: {
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.sm,
  },
  previewTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: colors.textPrimary,
  },
  previewSubtitle: {
    fontSize: 13,
    color: colors.textMuted,
    marginTop: 2,
  },
  imageWrapper: {
    flex: 1,
    backgroundColor: '#0F172A',
    margin: spacing.md,
    borderRadius: borderRadius.xl,
    overflow: 'hidden',
  },
  previewImage: {
    width: '100%',
    height: '100%',
  },
  previewActions: {
    flexDirection: 'row',
    gap: spacing.md,
    padding: spacing.lg,
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  retakeButton: {
    flex: 1,
    minHeight: 48,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.surfaceContainerLow,
    alignItems: 'center',
    justifyContent: 'center',
  },
  retakeText: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.textSecondary,
  },
  confirmButton: {
    flex: 2,
    minHeight: 48,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  confirmText: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.textLight,
  },
});
