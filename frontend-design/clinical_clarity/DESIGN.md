---
name: Clinical Clarity
colors:
  surface: '#faf8ff'
  surface-dim: '#d2d9f4'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3ff'
  surface-container: '#eaedff'
  surface-container-high: '#e2e7ff'
  surface-container-highest: '#dae2fd'
  on-surface: '#131b2e'
  on-surface-variant: '#3d4947'
  inverse-surface: '#283044'
  inverse-on-surface: '#eef0ff'
  outline: '#6d7a77'
  outline-variant: '#bcc9c6'
  surface-tint: '#006a61'
  primary: '#00685f'
  on-primary: '#ffffff'
  primary-container: '#008378'
  on-primary-container: '#f4fffc'
  inverse-primary: '#6bd8cb'
  secondary: '#006a63'
  on-secondary: '#ffffff'
  secondary-container: '#99efe5'
  on-secondary-container: '#006f67'
  tertiary: '#006194'
  on-tertiary: '#ffffff'
  tertiary-container: '#007bb9'
  on-tertiary-container: '#fdfcff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#89f5e7'
  primary-fixed-dim: '#6bd8cb'
  on-primary-fixed: '#00201d'
  on-primary-fixed-variant: '#005049'
  secondary-fixed: '#9cf2e8'
  secondary-fixed-dim: '#80d5cb'
  on-secondary-fixed: '#00201d'
  on-secondary-fixed-variant: '#00504a'
  tertiary-fixed: '#cce5ff'
  tertiary-fixed-dim: '#93ccff'
  on-tertiary-fixed: '#001d31'
  on-tertiary-fixed-variant: '#004b73'
  background: '#faf8ff'
  on-background: '#131b2e'
  surface-variant: '#dae2fd'
typography:
  display-lg:
    fontFamily: Manrope
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Manrope
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Manrope
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 38px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Manrope
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Manrope
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-xl:
    fontFamily: Manrope
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-lg:
    fontFamily: Manrope
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Manrope
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 22px
  body-bold:
    fontFamily: Manrope
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
  label-lg:
    fontFamily: Manrope
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Manrope
    fontSize: 13px
    fontWeight: '600'
    lineHeight: 18px
    letterSpacing: 0.02em
  caption:
    fontFamily: Manrope
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  touch-min: 3rem
  pad-xs: 0.25rem
  pad-sm: 0.5rem
  pad-md: 0.75rem
  pad-lg: 1rem
  pad-xl: 1.5rem
  pad-2xl: 2rem
  gap-grid: 1.5rem
  gutter-desktop: 2rem
  gutter-mobile: 1rem
---

## Brand & Style

This design system establishes an environment of clinical precision, calm authority, and radical accessibility. Built for healthcare practitioners, administrative staff, and patients—including elderly individuals or those under cognitive or physical distress—the interface prioritizes legibility, cognitive ease, and swift operational clarity.

The visual direction blends **Corporate / Modern** healthcare rigor with **Minimalist** clarity. Every screen eliminates decorative distractions, dark gradients, ambiguous iconography, and visual noise in favor of high-contrast data hierarchies, large tactile surfaces, and serene clinical tonality. The aesthetic evokes the quiet, sterile, yet comforting confidence of modern medical care: clean, reassuring, and immediate.

## Colors

The palette relies on clinically grounded hues engineered strictly for high-contrast accessibility (exceeding WCAG 2.1 AAA for text pairings wherever possible).

### Palette Roles
- **Primary Teal (`#0D9488`) & Primary Deep (`#0F766E`)**: Anchors primary calls to action, brand indicators, and key operational confirmations. Primary Deep is leveraged for high-contrast interactive states and links on light backgrounds.
- **Dark Navy (`#0F172A`) & Slate Text (`#1E293B`)**: Delivers crisp readability across all headers and core clinical data displays, bypassing pure black to reduce harsh optical glare on screens while maintaining maximum legibility.
- **Secondary Neutral Tint (`#64748B`)**: Dedicated to secondary meta-labels, timestamps, and de-emphasized structural hints.
- **Clinical Tints (`#F0FDFA`, `#E6F4F6`, `#F8FAFC`)**: Soft, hygienic background tones used for surface segmentation, hover states, active table rows, and callout containers.
- **Base White (`#FFFFFF`)**: Pure background plane providing stark contrast and sterile clarity.
- **Border Slate (`#CBD5E1`) & Focus Teal (`#0D9488`)**: Explicit, high-visibility boundaries ensuring form controls and card divisions are perceivable in clinical lighting. Focus outlines use a dedicated `#0D9488` with an outer white ring for unambiguous visibility.
- **Clinical Status**: Critical Alert (`#DC2626` / `#FEF2F2`), Warning (`#D97706` / `#FFFBEB`), and Positive (`#16A34A` / `#F0FDF4`).

## Typography

Typography relies uniformly on **Manrope**, selected for its open counters, balanced geometric architecture, and exceptional optical performance on bedside monitors, tablets, and handheld devices.

- **Baseline Body Scale**: The baseline body size never drops below 15px, with patient-facing text defaulting to 16px or 18px for instant legibility across age demographics.
- **Numbers and Clinical Metrics**: Formatted with tabular lining figures to ensure blood pressures, dosages, and telemetry stats align horizontally without rhythmic disruption.
- **Hierarchy Rules**: Dark Navy (`#0F172A`) is assigned to all headline and numerical values; secondary labels use `#64748B` at no less than 13px to ensure clinical safety.

## Layout & Spacing

The layout is governed by a patient-first, clinic-resilient fluid grid calibrated to an 8px base rhythm (with a 4px sub-grid for tight data groupings).

- **Touch & Click Target Threshold**: Any interactive target (buttons, toggles, row clicks, segmented controls) mandates a strict minimum touch area of **48x48px** (`touch-min`) to prevent mis-taps during high-urgency interactions or for tremor-affected hands.
- **Grid Structure**:
  - **Desktop (1024px+)**: 12-column responsive layout, 24px column gutters, 32px external margins, max container width 1440px.
  - **Tablet (640px – 1023px)**: 8-column layout, 20px gutters, 24px margins. Clinical charts and vital cards break into dual-column cards.
  - **Mobile (up to 639px)**: 4-column layout, 16px gutters, 16px margins. Complex multi-column tables convert to stacked detail cards.

## Elevation & Depth

This design system avoids theatrical drop shadows and dark moody gradients in favor of **low-contrast outlines** paired with **subtle clinical tonal layering**.

1. **Flat Base**: The default background sits at `#FFFFFF`. Primary containers and cards sit on `#FFFFFF` bordered by a crisp `1px solid #CBD5E1`.
2. **Surface Grouping**: Secondary clinical sections, input wells, and chart backgrounds employ `#F8FAFC` or `#F0FDFA` with seamless hairline borders, eliminating visual heaviness.
3. **Elevated Overlays (Dialogs, Menus, Alerts)**: When visual separation from the background is essential, surfaces use an ultra-diffused, cool-tinted shadow: `0 8px 24px -4px rgba(15, 23, 42, 0.08)`.
4. **Active & Focus Feedback**: Depth is communicated laterally through clear 2px to 3px solid borders in Primary Teal (`#0D9488`) rather than vertical extrusion.

## Shapes

The interface embraces a human-centric, friendly geometry calibrated at level `2` (Rounded):
- Standard interactive elements, inputs, and list rows maintain an outer curvature of **12px (`0.75rem`) to 16px (`1rem`)**.
- Modal dialogs, patient summary cards, and primary panels utilize **16px (`1rem`) to 20px (`1.25rem`)**.
- Chips and status tags utilize **24px / full pill** treatments to establish distinct visual delineation from angular interactive cards.
- Curved perimeters humanize the experience, softening anxiety-provoking medical flows while remaining structured and organized.

## Components

### Buttons
- **Primary**: Solid `#0D9488` with `#FFFFFF` text. Height: 48px minimum. Border radius: 12px. Hover: `#0F766E`. Active: Scale to 0.99 with deepening tone.
- **Secondary**: `#F0FDFA` background with 1px border in `#0D9488` and text in `#0F766E`.
- **Tertiary / Ghost**: Transparent background, text `#0F172A`, hover background `#F8FAFC`.
- **Focus Ring**: `0 0 0 3px rgba(13, 148, 136, 0.35)` with an inner offset of 2px.

### Inputs & Text Areas
- Height: 48px for single-line inputs.
- Background: `#FFFFFF`. Border: `1.5px solid #CBD5E1`. Radius: 12px.
- Text: `#0F172A` in 16px font to prevent auto-zoom on mobile web browsers.
- Placeholder: `#64748B`.
- Focus: Border shifts to `#0D9488` with a 3px soft teal halo (`rgba(13, 148, 136, 0.2)`).

### Chips & Status Badges
- Pill-shaped (fully rounded), height: 32px to 36px.
- Normal/Active: Background `#E6F4F6`, border `1px solid rgba(13, 148, 136, 0.3)`, text `#0F766E`, font-weight: 600.
- Warning: Background `#FFFBEB`, text `#B45309`, border `1px solid #FDE68A`.
- Critical/Urgent: Background `#FEF2F2`, text `#B91C1C`, border `1px solid #FECACA`.

### Checkboxes & Radio Buttons
- 24px x 24px hit footprint wrapped inside a 48px minimum touch area target.
- Checkbox radius: 6px; Radio radius: 50%.
- Unchecked: `#FFFFFF` with 2px border `#CBD5E1`.
- Checked: `#0D9488` solid fill with crisp white checkmark or center pip.

### Cards & Clinical Panels
- Background: `#FFFFFF`. Border: `1px solid #CBD5E1`. Corner radius: 16px.
- Internal padding: 20px (mobile) to 28px (desktop).
- Header integration: Clean separator border `#E2E8F0` or wrapped inside a `#F8FAFC` top compartment.

### Patient Data Lists & Tables
- Row height: Minimum 56px with generous horizontal cell padding.
- Alternating row interaction: Hover state triggers `#F0FDFA`. Selected state uses `#E6F4F6` with a 4px left-accent bar in `#0D9488`.
- Divider lines: Crisp 1px `#E2E8F0`.

### Medical Alerts & Callouts
- Bounded card with a 4px left border indicator (Teal, Amber, or Red).
- Background: Soft-tint matching tone (`#F0FDFA` for clinical notices, `#FEF2F2` for vital parameter deviations).
- Radius: 12px with high-contrast `#0F172A` content text.