# Profile Activity Legend Design

## Goal

Add a compact, always-visible legend to the Profile activity heatmap on both the Overview dashboard and the complete Profile view. The legend must explain the current mode's base token encoding and the four existing milestone tiers without competing with the heatmap.

## Approved Direction

Use the selected bottom compact legend (visual option A).

- In the complete Profile view, place the legend directly below the existing month labels and align it to the right edge of the 52-week grid.
- In Overview, which intentionally has no month-label row, place the legend directly below the grid without adding month labels.
- Keep the Overview version on one compact line with the lowest practical visual weight.
- Use the same content and behavior in the complete Profile view with slightly more breathing room.
- Keep the legend inside the existing horizontally scrollable activity area so narrow layouts do not increase page width.

## Mode-Aware Base Scale

The first legend segment changes with `profileActivityMode` so it accurately describes the rendered encoding.

- **Daily:** show `Less`, five square swatches from the empty/base tone through the strongest daily heat tone, then `More`.
- **Weekly:** show `Less`, a five-step ascending miniature column glyph, then `More`, because weekly totals are encoded by active column height rather than heat color.
- **Cumulative:** use the same ascending-column scale as Weekly because cumulative totals are also encoded by column height.

Decorative scale glyphs are hidden from assistive technology. The surrounding localized text describes the direction of the scale.

## Milestone Segment

After a subtle divider, always show four compact outlined badges:

- `100M` in the existing tier-1 cyan.
- `300M` in the existing tier-2 violet.
- `500M` in the existing tier-3 amber.
- `1B` in the existing tier-4 pink.

The badges reuse the existing `--profile-milestone-*` color tokens. They do not introduce a fifth milestone state, change threshold semantics, or replace the existing rings and tooltip badges. Numeric labels keep the tiers understandable without relying on color alone.

## Components and State

Add one reusable legend renderer or markup helper that accepts the current activity mode and the target surface. Both Overview and Profile call it from their existing mode-aware render paths.

- `profileActivityMode` remains the single page-session state.
- Changing Daily, Weekly, or Cumulative rerenders the relevant legend locally alongside the heatmap.
- No API request, cache mutation, persistence, or backend contract changes are introduced.
- Overview and Profile retain their existing namespaced DOM ownership while sharing legend semantics and CSS primitives.

## Layout and Responsive Behavior

- The legend width follows the existing grid's minimum width so its right edge remains aligned with the latest week.
- The Overview legend uses smaller gaps and badges than the complete Profile legend.
- On narrow screens, the legend scrolls with the grid and month labels inside the existing activity scroller.
- The legend must not create document-level horizontal overflow or cover the right-edge tooltip.
- Existing 52×7 geometry, 3 px grid gap, 2 px cell radius, and month label positions remain unchanged.

## Localization and Accessibility

- Add English and Simplified Chinese strings for `Less` and `More` if equivalent reusable keys do not already exist.
- Keep milestone badge values locale-neutral.
- Expose a concise localized legend label to assistive technology while marking individual decorative swatches and bars `aria-hidden="true"`.
- Preserve keyboard focus, tooltip accessible text, reduced-motion behavior, and theme contrast.

## Loading, Empty, and Error States

Render the legend only with the ready heatmap. Loading and unavailable states do not show a detached legend. An activity window with zero tokens still shows the legend because the empty/base scale remains meaningful.

## Testing and Verification

Frontend contract tests will cover:

- Overview and Profile each contain the compact legend host.
- Daily uses the five-square heat scale.
- Weekly and Cumulative use the ascending-column scale.
- All four milestone thresholds and existing milestone color tokens are represented.
- Mode changes keep both surfaces and their legend state synchronized.
- English and Simplified Chinese labels are present.
- Legend content stays inside the existing activity scroller.

Local browser verification will cover Daily, Weekly, and Cumulative in Overview and Profile; light and dark themes; English and Chinese; narrow and wide layouts; right-edge tooltips; and document-level horizontal overflow.

## Functional Impact and Compatibility

Intentional changes:

- Both activity surfaces gain an always-visible compact legend in the ready state.
- The legend's base scale changes between square heat swatches and ascending column glyphs when the shared mode changes.

Unchanged behavior:

- Token calculations, milestone thresholds, heat levels, aggregate heights, tooltip contents, activity geometry, mode synchronization, reload default, API responses, caching, KPIs, charts, and tables.

Primary regression risks are extra vertical height in Overview, misleading aggregate semantics, narrow-screen overflow, reduced tooltip room, and weak theme contrast. The compact right-aligned layout, mode-aware glyphs, existing scroller ownership, viewport tooltip checks, and theme verification mitigate these risks.

## Out of Scope

- Changing milestone thresholds or Tier Aura styling.
- Adding configurable or collapsible legends.
- Persisting the selected activity mode.
- Adding the separate Last Week date preset.
