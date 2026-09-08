import { TextStyle } from 'react-native';
import colors from './colors';

export const typography: Record<string, TextStyle> = {
  h1: {
    fontSize: 26,
    fontWeight: '700',
    color: colors.onSurface,
    letterSpacing: -0.5,
  },
  h2: {
    fontSize: 22,
    fontWeight: '700',
    color: colors.onSurface,
    letterSpacing: -0.3,
  },
  h3: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.onSurface,
  },
  subtitle: {
    fontSize: 15,
    fontWeight: '500',
    color: colors.textSecondary,
    lineHeight: 22,
  },
  body: {
    fontSize: 14,
    fontWeight: '400',
    color: colors.onSurface,
    lineHeight: 20,
  },
  bodyMedium: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.onSurface,
    lineHeight: 20,
  },
  caption: {
    fontSize: 12,
    fontWeight: '400',
    color: colors.textSecondary,
    lineHeight: 16,
  },
  captionBold: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.textSecondary,
    lineHeight: 16,
  },
  button: {
    fontSize: 15,
    fontWeight: '600',
    letterSpacing: 0.2,
  },
};

export default typography;
