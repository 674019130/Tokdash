# Overview Profile Modes and Token Milestones Design

**Status:** Approved in conversation on 2026-07-27 for local implementation on `feat/profile-stats-view`.

## Context

The Overview page now contains a compact 52-week Profile activity band, while the complete Stats → Profile view supports Daily, Weekly, and Cumulative activity modes. Overview currently renders Daily only. Users should be able to explore all three modes directly from Overview, and the two surfaces should behave as one coherent Profile experience.

Large token totals should also feel meaningfully different without replacing the heatmap's existing intensity encoding. Four milestone levels—100 million, 300 million, 500 million, and 1 billion tokens—will add a restrained secondary visual layer and richer hover/focus feedback.

This design intentionally updates two constraints in `2026-07-27-overview-profile-summary-design.md`: Overview will now have mode controls, and navigation between Overview and Profile will preserve one shared activity mode.

## Goals

- Add Daily, Weekly, and Cumulative controls to the Overview Profile band.
- Keep the selected mode synchronized between Overview and the complete Profile view.
- Apply consistent milestone semantics to Daily, Weekly, and Cumulative values.
- Use the approved Tier Aura direction: preserve heat meaning and add tier-specific rings, glow, and tooltip treatment.
- Keep Overview compact and visually subordinate to its KPIs and charts.
- Reuse existing cached Profile data and pure aggregation functions without a new request or backend change.

## Non-goals

- User-configurable milestone thresholds or colors.
- Persisting the selected mode across page reloads or browser sessions.
- Changing the 52-week window, heat-level calculation, streak calculation, or token totals.
- Adding milestone notifications, badges outside the activity surface, or gamification history.
- Adding continuous decorative animation. Motion is limited to the existing short hover/focus response and is disabled when reduced motion is requested.
- Changing `/api/usage`, `/api/stats`, or stored data formats.

## View Interaction

The Overview heatmap header gains three small pill buttons: Daily, Weekly, and Cumulative. They use the existing Profile mode-control styling at the Overview's smaller visual scale.

Overview and the complete Profile view share the in-memory `profileActivityMode` state:

- Switching a mode in either surface immediately updates that surface without a network request.
- Entering the other surface renders it in the same selected mode.
- Both surfaces expose the same `aria-pressed` state whenever they render.
- Reloading the page keeps the existing default of Daily; no `localStorage` or URL state is added.

The Overview range copy becomes `Past 52 weeks` rather than `Past 52 weeks · Daily`, because the pressed control now communicates the active mode. Existing English and Simplified Chinese mode labels are reused.

## Aggregation Semantics

Milestone classification uses the token value represented by the current visual unit:

| Mode | Visual unit | Value used for milestone classification |
| --- | --- | --- |
| Daily | One day square | That day's token total |
| Weekly | One seven-cell column | That week's token total |
| Cumulative | One seven-cell column | Running token total through that week |

Thresholds are inclusive and evaluated from highest to lowest:

| Tier | Minimum tokens | Label | Visual tone |
| --- | ---: | --- | --- |
| 4 | 1,000,000,000 | `1B+` | Pink with a white double ring |
| 3 | 500,000,000 | `500M+` | Gold with a stronger double halo |
| 2 | 300,000,000 | `300M+` | Violet with a medium halo |
| 1 | 100,000,000 | `100M+` | Cyan with a light single ring |

Values below 100 million have no milestone. Future days and empty aggregates never receive a milestone. Because Cumulative uses the running total, a column remains in its achieved tier until a later column enters a higher tier.

The classification is provided by a pure helper so exact threshold boundaries and all three aggregation modes can be tested independently from the DOM.

## Tier Aura Visual System

The approved visual direction is Tier Aura.

The existing heatmap fill remains the primary representation of relative activity. Milestones add semantic CSS variables for tier color, ring, and glow; they do not replace the base heat level or aggregate geometry.

### Daily

The qualifying day square receives its tier ring and a low-intensity resting glow. Hover or keyboard focus lifts it by one pixel, brightens the ring, and expands the glow. Overview uses a quieter glow than the complete Profile view.

### Weekly and Cumulative

The top active cell of each aggregate column carries the tier ring. Hover or keyboard focus on the column's existing transparent hit target strengthens the tier treatment and continues to highlight the entire column. In Cumulative mode, resting rings remain deliberately subtle so a run of already-achieved columns does not become a solid neon band.

### Theme and Motion Behavior

Four milestone CSS custom properties define the semantic palette, with theme-specific contrast adjustments where necessary. Ring width and luminance, not hue alone, distinguish levels. Under `prefers-reduced-motion: reduce`, the one-pixel lift and animated transitions are removed while ring and focus visibility remain.

## Tooltip and Accessible Feedback

The existing structured Profile tooltip model gains optional milestone metadata. A qualifying tooltip adds:

- A tier-colored `100M+`, `300M+`, `500M+`, or `1B+` badge in the header.
- Stronger tier-colored emphasis for the total token value.
- The existing date/range, token breakdown, and estimated cost rows unchanged.

The full milestone label is included in the target's accessible text. Hover and keyboard focus produce the same information. Non-qualifying cells use the existing tooltip DOM and appearance without an empty badge or layout gap.

Tooltip rendering continues to use safe DOM construction and the correct namespaced tooltip element for each surface. Viewport collision handling must keep the richer tooltip visible for milestone cells near the right and top edges.

## Components and Data Flow

### Shared State and Pure Data

- `profileActivityMode` remains the single page-session mode state.
- `setProfileActivityMode(mode)` validates the mode and rerenders whichever activity surface is active.
- The Overview preview builder accepts the selected mode instead of hard-coding Daily.
- The existing `buildProfileActivityCells(mode, days, weeks)` output is reused for Daily and aggregate geometry.
- A pure milestone helper classifies the represented token value and enriches render definitions or tooltip models without changing API data.

### Overview Renderer

Overview keeps its separate namespaced renderer because its metrics, density, loading state, and DOM IDs differ from the complete Profile view. It gains:

- Three namespaced mode buttons.
- A namespaced 52-column aggregate hit-target layer for Weekly and Cumulative.
- Namespaced column-hover handling.
- Mode-aware cells and tooltip models.

Daily renders 364 focusable or future-disabled day cells. Weekly and Cumulative render the same 364 visual squares plus 52 focusable column hit targets, matching the complete Profile interaction pattern.

### Complete Profile Renderer

The complete Profile renderer keeps its current layout and controls. It consumes the same milestone helper and tooltip metadata, but may use the slightly stronger Profile-scale aura defined by CSS. No new fetch is performed when the mode changes.

### Requests and Caching

The Overview band continues to consume the existing scheduled `/api/stats` warm response and `statsCache.default`. Switching modes performs only local aggregation and DOM replacement. Loading, empty, unavailable, retry, and re-entry behavior remain unchanged.

## Responsive Behavior

- On wide screens, Overview mode controls sit on the right side of the activity header.
- At narrow widths, the header may wrap controls onto a second line without increasing the band more than necessary.
- The 52-column square-cell grid retains its 3 px gap and 2 px corner radius.
- If the grid cannot fit legibly, it keeps the existing horizontal scroller and initial scroll to the most recent edge.
- Tooltip content clamps to the viewport rather than increasing page width.

## Localization

Daily, Weekly, Cumulative, and the existing range/tooltip vocabulary reuse current English and Simplified Chinese translations. Numeric milestone badges remain locale-neutral. Any explanatory milestone text added to accessible labels receives both translations.

## Accessibility

- All six mode buttons use `aria-pressed` and retain visible focus treatment.
- Daily milestone cells remain keyboard-focusable buttons.
- Weekly and Cumulative retain one keyboard-focusable hit target per column.
- Tier levels differ by ring structure and badge text as well as hue.
- Tooltip content is represented in each target's accessible label and is not hover-only.
- Reduced-motion preferences remove transforms and nonessential transitions.
- Empty and loading states do not expose inactive mode content as interactive.

## Testing and Verification

Pure-function tests will cover:

- One value below, exactly at, and immediately above each milestone threshold.
- Highest-tier-first classification.
- Daily, Weekly, and Cumulative token sources.
- Cumulative tier retention and upgrades.
- Empty, future, missing, negative, and non-numeric values.

Frontend tests will cover:

- Overview's three namespaced buttons and pressed states.
- Shared mode state when moving Overview → Profile and Profile → Overview.
- No fetch triggered by mode changes.
- Daily cells versus Weekly/Cumulative hit targets and column hover.
- Milestone metadata in tooltips and accessible labels.
- Non-milestone tooltip output remaining unchanged.
- Responsive overflow, theme tokens, and reduced-motion CSS.
- The existing loading, error, empty, and warm-cache paths.

Local browser verification will cover all three modes and all four tiers in light/dark themes, English/Chinese, wide/narrow layouts, keyboard navigation, right-edge tooltip positioning, and movement between Overview and Profile. Relevant tests, lint, and the repository's applicable type check will run before handoff; any pre-existing type-check failure will be reported with its exact command and diagnostics.

## Functional Impact and Regression Risks

Intentional behavior changes from the previous Overview Profile summary are:

- Overview changes from a Daily-only preview to three locally switchable modes.
- Overview and Profile now share the selected mode instead of behaving independently.
- Opening the full Profile preserves the mode selected on Overview.
- The Overview range subtitle no longer contains a fixed `Daily` suffix.
- Qualifying activity units gain milestone rings and richer tooltips on both surfaces.

Backend responses, selected-range Overview KPIs, charts, tables, Profile calculations, and default-on-reload behavior remain compatible.

Primary regression risks are:

- stale pressed states when switching surfaces;
- duplicated Overview/Profile DOM IDs or tooltip ownership;
- Cumulative milestone runs becoming visually dominant;
- aggregate hit targets drifting out of alignment with square columns;
- richer right-edge tooltips creating overflow;
- milestone styling reducing contrast in a theme;
- mode rerenders interfering with initial horizontal scroll or loading/error states.

Shared state, pure classification, namespaced Overview controls, subtle cumulative resting treatment, existing grid geometry, viewport-aware tooltip placement, theme checks, and explicit regression tests mitigate these risks.
