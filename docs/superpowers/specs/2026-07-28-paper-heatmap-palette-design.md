# Paper Heatmap and Milestone Palette Design

**Status:** Approved in conversation on 2026-07-28 for local implementation on `feat/profile-stats-view`.

## Context

Tokdash's Paper theme currently uses a warm beige-to-brown heat scale that ends in slate, while the Profile milestone aura uses the same cyan, violet, amber, and pink palette as every other theme. The two systems are individually readable but do not feel like one visual language. The milestone hues can also compete with the underlying Daily heat level, especially on darker day cells.

The approved redesign treats the base heat scale and the Profile milestone aura as two coordinated layers:

- **Slate Ink** becomes the Paper theme's base heat palette.
- **Mineral Spectrum** becomes the Paper theme's milestone palette.
- A one-pixel Paper-colored inner keyline separates milestone aura from the underlying heat fill.

The visual comparison considered Warm Ink, Sepia Paper, and Slate Ink for the base scale; Slate Ink was selected. It then considered Paper Native, Mineral Spectrum, Aurora Bloom, and Metal & Ember for the aura; Mineral Spectrum was selected.

## Goals

- Give every Paper heatmap a smooth, theme-appropriate Slate Ink activity scale.
- Keep base heat intensity legible underneath all four milestone tiers.
- Give Paper Light and Paper Dark separate milestone colors instead of sharing one palette.
- Keep the milestone mapping consistent across activity cells, Overview, legends, tooltips, hover, and keyboard focus.
- Preserve all token calculations, heat-level calculations, milestone thresholds, aggregate geometry, and data contracts.
- Leave all nine non-Paper themes visually and functionally unchanged.

## Non-goals

- Changing the 100M, 300M, 500M, or 1B milestone thresholds.
- Adding a 10B milestone.
- Changing Daily relative-level boundaries, Month/Year/3D quantile logic, Weekly/Cumulative height encoding, or the 52-week window.
- Changing chart palettes, KPI colors, cost/message colors, or the overall Paper theme outside heatmaps and Profile milestone treatment.
- Adding user-configurable colors, persistence, animation, or new settings.
- Adding the separate Last Week range preset.

## Approved Base Heat Palette: Slate Ink

Update only `heatColorsMap.paper` in `src/tokdash/static/theme-config.js`.

### Paper Light

| Heat index | Color | Role |
| ---: | --- | --- |
| 0 | `#F3EFE8` | Empty / paper neutral |
| 1 | `#E8E7E4` | Faint activity |
| 2 | `#DCE0E2` | Low activity |
| 3 | `#C8D0D4` | Low-mid activity |
| 4 | `#B4BEC4` | Medium activity |
| 5 | `#778995` | Medium-high activity |
| 6 | `#5D7180` | High activity |
| 7 | `#42596A` | Strongest / slate ink |

### Paper Dark

| Heat index | Color | Role |
| ---: | --- | --- |
| 0 | `#191716` | Empty / dark paper neutral |
| 1 | `#222629` | Faint activity |
| 2 | `#2B3034` | Low activity |
| 3 | `#384148` | Low-mid activity |
| 4 | `#4C5A64` | Medium activity |
| 5 | `#8399A7` | Medium-high activity |
| 6 | `#A6BAC4` | High activity |
| 7 | `#CDDCE3` | Strongest / light slate ink |

The existing consumers continue to interpret the palette as they do today:

- Month, Year, and 3D use all eight entries with their existing quantile thresholds.
- Profile Daily keeps five relative levels. `getProfileActivityColor()` maps levels 0–4 to heat indices 0, 2, 4, 5, and 7, producing the approved five visible colors.
- Profile Weekly and Cumulative continue to encode magnitude through column height. Active aggregate cells use the strongest heat color; empty cells use the first heat color.
- The heat legends continue to read from `HEAT_COLORS`, so they update without separate hard-coded swatches.

No calculation or threshold changes accompany the palette change.

## Approved Milestone Palette: Mineral Spectrum

The existing milestone level numbers, labels, and semantics remain unchanged. Paper receives theme-scoped CSS custom-property overrides.

| Tier | Threshold | Paper Light | Paper Dark | Material name |
| ---: | ---: | --- | --- | --- |
| 1 | 100M | `#3E8C78` | `#75C2AC` | Jade |
| 2 | 300M | `#557AA2` | `#8FB1D4` | Sapphire |
| 3 | 500M | `#C18A35` | `#E2B458` | Amber |
| 4 | 1B | `#B85466` | `#EA8798` | Garnet |

Add the Paper Light variables under `html[data-ui-theme="paper"]` and the Paper Dark variables under `html.dark[data-ui-theme="paper"]` in `src/tokdash/static/themes.css`. Scope the variables to `.profile-activity-shell` and `.overview-profile-band` so unrelated Paper components do not inherit Profile milestone semantics.

The cyan/violet/amber/pink variables already declared on the Profile surfaces remain the default fallback. Every non-Paper theme therefore keeps its current milestone colors.

## Aura, Keyline, and Surface Behavior

Milestone hue remains a secondary encoding layered over the base heat fill. The existing tier progression remains intact:

- 100M uses the quietest single ring.
- 300M adds a small glow.
- 500M uses the stronger double-halo treatment.
- 1B keeps the strongest ring and glow.
- Hover, keyboard focus, and aggregate column hover keep the current stronger treatment.
- Overview keeps its existing reduced aura intensity so the compact band does not compete with primary dashboard content.

Paper adds a one-pixel inset keyline using its current background color. The keyline visually separates Mineral Spectrum from Slate Ink at every heat level. Implement it through a semantic `--profile-milestone-keyline` variable:

- The default value is transparent, preserving every non-Paper theme.
- Paper Light and Dark set it to the current Paper background token.
- Milestone cell shadows place the inset keyline before the existing tier rings and glows.

Tooltip badges, prominent token rows, focus outlines, and legend badges already consume `--profile-milestone-*`; they automatically receive the selected Paper palette. The numeric labels `100M`, `300M`, `500M`, and `1B` remain visible, so milestone identity does not rely on color alone.

## Components and Data Flow

### Theme Heat Configuration

`theme-config.js` remains the single source for base heat colors. Existing theme selection calls `getHeatColors()` and refreshes the shared `HEAT_COLORS` array. Month, Year, 3D, Profile, and their legends continue to consume that array through their current render paths.

### Theme-scoped Milestone Tokens

`themes.css` owns the new Paper Light/Dark milestone overrides because the values are presentation tokens selected by the root theme and color mode. Existing Profile CSS in `index.html` continues to own ring geometry, glow intensity, hover/focus behavior, tooltip treatment, and compact Overview variants.

This separation keeps responsibilities narrow:

- JavaScript theme configuration chooses the base heat scale.
- Theme CSS chooses Paper-specific milestone hues and keyline color.
- Existing Profile CSS defines how a tier is rendered.
- Existing JavaScript continues to classify token values and attach semantic tier metadata.

There are no new requests, state variables, DOM attributes, persisted settings, or backend fields.

## Loading, Empty, and Error Behavior

- Loading and unavailable states remain unchanged and do not render a detached palette treatment.
- Empty heat cells use the first Slate Ink entry in Paper.
- Invalid or missing theme configuration continues through the existing heat-color fallback.
- Profile surfaces without a Paper theme match continue using their existing default milestone variables.
- Missing or non-qualifying milestone values continue to render without rings, glows, or badges.

## Accessibility and Motion

- Keep numeric milestone labels in the legend, tooltip, and accessible target text.
- Preserve visible keyboard focus and the existing parity between hover and focus feedback.
- Preserve `prefers-reduced-motion` behavior; this design adds no animation.
- Verify that all five visible Profile Daily levels remain distinguishable in Paper Light and Dark.
- Verify that each Mineral Spectrum tier remains visible on both the lightest and darkest base heat cells.
- Do not use the new colors for essential standalone text without the existing labels or semantic structure.

## Testing and Verification

Frontend contract tests will cover:

- The exact eight Paper Light and Paper Dark heat colors.
- The unchanged heat arrays for at least one representative non-Paper theme.
- Profile Daily's existing five-level mapping against the updated Paper array.
- Weekly and Cumulative still using empty/strong colors plus height encoding.
- Exact Paper Light/Dark milestone variables and the transparent non-Paper keyline fallback.
- All four milestone selectors, tooltip rows, and legend badges continuing to reuse semantic milestone variables.
- Existing milestone thresholds, labels, tooltip metadata, and accessible text remaining unchanged.

Local browser verification will cover:

- Paper Light and Dark in Profile Daily, Weekly, and Cumulative.
- Paper Light and Dark in the compact Overview activity band.
- Paper Month, Year, and 3D heatmaps and legends.
- 100M, 300M, 500M, and 1B on multiple underlying heat levels.
- Resting, hover, keyboard-focus, aggregate-column-hover, tooltip, and legend states.
- Wide and narrow layouts, right-edge tooltip collision handling, and document-level horizontal overflow.
- Runtime switching between Paper Light/Dark and a representative unchanged theme such as Classic.

Run the targeted Profile frontend tests, the full test suite, and the repository's exact compile check. Run the configured type check and lint if present; if the repository still has no configured targets, record the discovery command. Report any pre-existing failures with their exact command and diagnostics.

## Functional Impact and Compatibility

Intentional visual changes:

- Every Paper Month, Year, 3D, Profile, and associated heat legend uses Slate Ink.
- Paper Profile milestone cells, tooltips, and legends use Mineral Spectrum with Light/Dark variants.
- Paper milestone cells gain a one-pixel background keyline.

Unchanged behavior:

- API responses, token aggregation, costs, messages, dates, streaks, Profile summaries, heat thresholds, milestone thresholds, mode synchronization, tooltips' data, caching, and persistence.
- Cell geometry, 3 px gaps, 2 px Profile corner radius, responsive scrollers, aggregate hit targets, and accessibility semantics.
- All non-Paper theme heat and milestone palettes.

Primary regression risks are accidental global milestone overrides, weak contrast at a heat-scale endpoint, stale colors after runtime theme switching, mismatch between a heatmap and its legend, and Paper's global heat palette changing more surfaces than intended. Theme-scoped selectors, the existing shared `HEAT_COLORS` source, exact palette tests, endpoint visual checks, and explicit Month/Year/3D/Profile verification mitigate these risks.

## Out of Scope

- Any change to non-Paper palettes.
- Any new milestone threshold, notification, achievement history, or gamification surface.
- Any structural redesign of Overview or Profile.
- Any Last Week preset or date-range behavior change.
