/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Clinical Clarity Design Tokens (PRIMARY VISUAL SOURCE OF TRUTH)
        primary: '#00685f',
        'on-primary': '#ffffff',
        'primary-container': '#008378',
        'on-primary-container': '#f4fffc',
        'inverse-primary': '#6bd8cb',
        'primary-fixed': '#89f5e7',
        'primary-fixed-dim': '#6bd8cb',

        secondary: '#006a63',
        'on-secondary': '#ffffff',
        'secondary-container': '#99efe5',
        'on-secondary-container': '#006f67',
        'secondary-fixed': '#9cf2e8',
        'secondary-fixed-dim': '#80d5cb',

        tertiary: '#006194',
        'on-tertiary': '#ffffff',
        'tertiary-container': '#007bb9',
        'on-tertiary-container': '#fdfcff',

        background: '#faf8ff',
        'on-background': '#131b2e',

        surface: '#faf8ff',
        'on-surface': '#131b2e',
        'surface-dim': '#d2d9f4',
        'surface-bright': '#faf8ff',
        'surface-variant': '#dae2fd',
        'on-surface-variant': '#3d4947',

        'surface-container-lowest': '#ffffff',
        'surface-container-low': '#f2f3ff',
        'surface-container': '#eaedff',
        'surface-container-high': '#e2e7ff',
        'surface-container-highest': '#dae2fd',

        'inverse-surface': '#283044',
        'inverse-on-surface': '#eef0ff',

        outline: '#6d7a77',
        'outline-variant': '#bcc9c6',

        error: '#ba1a1a',
        'on-error': '#ffffff',
        'error-container': '#ffdad6',
        'on-error-container': '#93000a',
      },
      fontFamily: {
        sans: ['Manrope', 'sans-serif'],
      },
      boxShadow: {
        card: '0 2px 12px rgba(19, 27, 46, 0.06)',
        'card-hover': '0 8px 24px rgba(19, 27, 46, 0.12)',
        emergency: '0 0 30px rgba(186, 26, 26, 0.35)',
      },
    },
  },
  plugins: [],
};
