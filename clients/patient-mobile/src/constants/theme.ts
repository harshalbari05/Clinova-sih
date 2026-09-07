/**
 * Clinova Patient Mobile Design System & Theme Tokens
 * Direct translation of the approved design language from Clinova-sih/frontend-design/
 */

export const colors = {
  // Brand Teals (Primary)
  primary: '#00685F',
  primaryDark: '#004D46',
  primaryLight: '#E6F4F2',
  primaryBorder: '#BCE3DF',
  primaryGradientStart: '#004D46',
  primaryGradientEnd: '#00706B',
  onPrimary: '#FFFFFF',
  onPrimaryContainer: '#F4FFFC',
  primaryContainer: '#008378',

  // Secondary & Accents
  secondary: '#006A63',
  secondaryContainer: '#99EFE5',
  onSecondary: '#FFFFFF',
  onSecondaryContainer: '#006F67',
  tealAccent: '#0D9488',
  emerald: '#10B981',
  emeraldLight: '#ECFDF5',
  emeraldBorder: '#A7F3D0',

  // Neutrals & Surfaces (matching frontend-design)
  background: '#FAF8FF',
  surface: '#FAF8FF',
  surfaceContainerLowest: '#FFFFFF',
  surfaceContainerLow: '#F1F5F9',
  surfaceContainer: '#EAEDFF',
  surfaceContainerHigh: '#E2E8F0',
  surfaceContainerHighest: '#DAE2FD',
  border: '#E2E8F0',
  borderSubtle: '#F1F5F9',
  outline: '#6D7A77',
  outlineVariant: '#BCC9C6',

  // Text & Icons
  textPrimary: '#0F172A',
  textSecondary: '#334155',
  textMuted: '#64748B',
  textSubtle: '#94A3B8',
  textLight: '#FFFFFF',
  onSurface: '#131B2E',
  onSurfaceVariant: '#3D4947',

  // Alerts & Clinical Safety
  error: '#BA1A1A',
  errorContainer: '#FFDAD6',
  onError: '#FFFFFF',
  onErrorContainer: '#93000A',
  warning: '#D97706',
  warningContainer: '#FEF3C7',
  onWarningContainer: '#78350F',
  info: '#0284C7',
  infoContainer: '#E0F2FE',
  onInfoContainer: '#0369A1',
};

export const typography = {
  fontFamily: 'System',
  heading: {
    display: { fontSize: 32, fontWeight: '800' as const, lineHeight: 40 },
    h1: { fontSize: 24, fontWeight: '800' as const, lineHeight: 32 },
    h2: { fontSize: 20, fontWeight: '700' as const, lineHeight: 28 },
    h3: { fontSize: 17, fontWeight: '700' as const, lineHeight: 24 },
  },
  body: {
    large: { fontSize: 16, fontWeight: '400' as const, lineHeight: 24 },
    largeBold: { fontSize: 16, fontWeight: '700' as const, lineHeight: 24 },
    medium: { fontSize: 14, fontWeight: '500' as const, lineHeight: 20 },
    mediumBold: { fontSize: 14, fontWeight: '700' as const, lineHeight: 20 },
    small: { fontSize: 12, fontWeight: '500' as const, lineHeight: 16 },
    caption: { fontSize: 11, fontWeight: '600' as const, lineHeight: 14 },
  },
  // Aliases matching frontend-design HTML
  displayLg: { fontSize: 32, fontWeight: '800' as const, lineHeight: 40 },
  headlineLg: { fontSize: 26, fontWeight: '800' as const, lineHeight: 34 },
  headlineMd: { fontSize: 22, fontWeight: '700' as const, lineHeight: 30 },
  headlineSm: { fontSize: 19, fontWeight: '700' as const, lineHeight: 26 },
  bodyXl: { fontSize: 18, fontWeight: '400' as const, lineHeight: 26 },
  bodyLg: { fontSize: 16, fontWeight: '400' as const, lineHeight: 24 },
  bodyBold: { fontSize: 16, fontWeight: '700' as const, lineHeight: 24 },
  bodyMd: { fontSize: 14, fontWeight: '400' as const, lineHeight: 20 },
  labelLg: { fontSize: 14, fontWeight: '700' as const, lineHeight: 20 },
  labelMd: { fontSize: 13, fontWeight: '600' as const, lineHeight: 18 },
  caption: { fontSize: 11, fontWeight: '600' as const, lineHeight: 15 },
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
  xxxl: 32,
};

export const borderRadius = {
  sm: 6,
  md: 10,
  lg: 14,
  xl: 18,
  xxl: 24,
  full: 9999,
};

export const shadows = {
  card: {
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  elevated: {
    shadowColor: '#004D46',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 4,
  },
  modal: {
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.25,
    shadowRadius: 24,
    elevation: 10,
  },
  // Aliases
  sm: {
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  md: {
    shadowColor: '#004D46',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 4,
  },
  lg: {
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.25,
    shadowRadius: 24,
    elevation: 10,
  },
};
