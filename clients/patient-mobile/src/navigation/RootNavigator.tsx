import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { colors, spacing, borderRadius, typography, shadows } from '../constants/theme';
import { useAuth } from '../context/AuthContext';
import { AuthScreen } from '../screens/AuthScreen';
import { HomeScreen } from '../screens/HomeScreen';
import { IntakeScreen } from '../screens/IntakeScreen';
import { DocumentsScreen } from '../screens/DocumentsScreen';
import { TimelineScreen } from '../screens/TimelineScreen';
import { SummaryScreen } from '../screens/SummaryScreen';
import { ProfileScreen } from '../screens/ProfileScreen';

export type ScreenName = 'Home' | 'Intake' | 'Documents' | 'Timeline' | 'Summary' | 'Profile';

interface TabItem {
  key: ScreenName;
  label: string;
  emoji: string;
}

const TABS: TabItem[] = [
  { key: 'Home', label: 'Home', emoji: '🏠' },
  { key: 'Intake', label: 'Intake', emoji: '📋' },
  { key: 'Documents', label: 'Documents', emoji: '📄' },
  { key: 'Timeline', label: 'Timeline', emoji: '📈' },
  { key: 'Profile', label: 'Profile', emoji: '👤' },
];

export const RootNavigator: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [currentScreen, setCurrentScreen] = useState<ScreenName>('Home');
  const [history, setHistory] = useState<ScreenName[]>(['Home']);

  const navigate = (screen: ScreenName) => {
    setHistory((prev) => [...prev, screen]);
    setCurrentScreen(screen);
  };

  const goBack = () => {
    if (history.length > 1) {
      const nextHistory = [...history];
      nextHistory.pop(); // Remove current
      const prevScreen = nextHistory[nextHistory.length - 1];
      setHistory(nextHistory);
      setCurrentScreen(prevScreen);
    } else {
      setCurrentScreen('Home');
    }
  };

  const navigationProp = {
    navigate,
    goBack,
    currentScreen,
  };

  // 1. Session restoration loading splash
  if (isLoading) {
    return (
      <View style={styles.splashContainer}>
        <View style={styles.splashLogoCircle}>
          <Text style={styles.splashLogoText}>CLINOVA</Text>
        </View>
        <ActivityIndicator size="large" color={colors.primary} style={{ marginTop: 24 }} />
        <Text style={styles.splashText}>Restoring secure session...</Text>
        <Text style={styles.splashSub}>Connected to Clinova Health Cloud</Text>
      </View>
    );
  }

  // 2. Route protection: If unauthenticated, render AuthScreen
  if (!isAuthenticated) {
    return <AuthScreen />;
  }

  // 3. Render active authenticated screen
  const renderScreen = () => {
    switch (currentScreen) {
      case 'Home':
        return (
          <HomeScreen
            navigation={navigationProp}
            onStartConsultation={() => navigate('Intake')}
            onNavigateToTimeline={() => navigate('Timeline')}
            onNavigateToDocuments={() => navigate('Documents')}
          />
        );
      case 'Intake':
        return (
          <IntakeScreen
            navigation={navigationProp}
            onFinishIntake={() => navigate('Summary')}
            onNavigateToDocuments={() => navigate('Documents')}
            onNavigateToTimeline={() => navigate('Timeline')}
          />
        );
      case 'Documents':
        return (
          <DocumentsScreen
            navigation={navigationProp}
            onNavigateToIntake={() => navigate('Intake')}
            onNavigateToTimeline={() => navigate('Timeline')}
          />
        );
      case 'Timeline':
        return (
          <TimelineScreen
            navigation={navigationProp}
            onNavigateToDocuments={() => navigate('Documents')}
            onNavigateToIntake={() => navigate('Intake')}
          />
        );
      case 'Summary':
        return (
          <SummaryScreen
            navigation={navigationProp}
            onNavigateToHome={() => navigate('Home')}
            onNavigateToIntake={() => navigate('Intake')}
            onNavigateToDocuments={() => navigate('Documents')}
          />
        );
      case 'Profile':
        return (
          <ProfileScreen
            navigation={navigationProp}
            onNavigateToHome={() => navigate('Home')}
          />
        );
      default:
        return (
          <HomeScreen
            navigation={navigationProp}
            onStartConsultation={() => navigate('Intake')}
            onNavigateToTimeline={() => navigate('Timeline')}
            onNavigateToDocuments={() => navigate('Documents')}
          />
        );
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.screenContainer}>{renderScreen()}</View>

      {/* Fixed Bottom Navigation Bar matching clinova_patient_dashboard */}
      <View style={styles.bottomNav}>
        <View style={styles.bottomNavGrid}>
          {TABS.map((tab) => {
            const isActive = currentScreen === tab.key;
            return (
              <TouchableOpacity
                key={tab.key}
                style={styles.tabBtn}
                onPress={() => navigate(tab.key)}
                activeOpacity={0.7}
              >
                <View
                  style={[
                    styles.tabIconCircle,
                    isActive && styles.tabIconCircleActive,
                  ]}
                >
                  <Text style={styles.tabEmoji}>{tab.emoji}</Text>
                </View>
                <Text
                  style={[
                    styles.tabLabel,
                    isActive && styles.tabLabelActive,
                  ]}
                >
                  {tab.label}
                </Text>
                {isActive && <View style={styles.activeDot} />}
              </TouchableOpacity>
            );
          })}
        </View>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.surface,
  },
  screenContainer: {
    flex: 1,
  },
  splashContainer: {
    flex: 1,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
  },
  splashLogoCircle: {
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.xxl,
    backgroundColor: colors.surfaceContainerLowest,
    borderWidth: 2,
    borderColor: colors.primary,
    ...shadows.md,
  },
  splashLogoText: {
    ...typography.headlineLg,
    color: colors.primary,
    fontWeight: '800',
    letterSpacing: 2,
  },
  splashText: {
    ...typography.bodyBold,
    color: colors.onSurface,
    marginTop: spacing.md,
  },
  splashSub: {
    ...typography.caption,
    color: colors.onSurfaceVariant,
    marginTop: spacing.xs,
  },
  bottomNav: {
    backgroundColor: 'rgba(255, 255, 255, 0.96)',
    borderTopWidth: 1,
    borderTopColor: colors.outlineVariant,
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.sm,
    ...shadows.md,
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
  },
  bottomNavGrid: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
  },
  tabBtn: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 2,
  },
  tabIconCircle: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'transparent',
  },
  tabIconCircleActive: {
    backgroundColor: colors.surfaceContainerLow,
  },
  tabEmoji: {
    fontSize: 18,
  },
  tabLabel: {
    fontSize: 10,
    fontWeight: '600',
    color: colors.onSurfaceVariant,
    marginTop: 1,
  },
  tabLabelActive: {
    color: colors.primary,
    fontWeight: '800',
  },
  activeDot: {
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: colors.primary,
    marginTop: 2,
  },
});
