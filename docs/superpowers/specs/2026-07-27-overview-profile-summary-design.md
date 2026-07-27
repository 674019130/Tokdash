# Overview Profile Summary Design

**Status:** Approved in conversation on 2026-07-27 for local implementation on `feat/profile-stats-view`.

## Context

The new Stats → Profile view provides a complete 52-week activity experience with five summary metrics and Daily, Weekly, and Cumulative modes. The Overview page should make that experience discoverable without duplicating it or weakening Overview's existing selected-range KPIs, charts, and breakdown tables.

The approved direction is a compact, full-width Profile activity band placed after the two Overview charts and before the breakdown tables. It is a bridge from aggregate Overview information to detailed tables, not a second Profile page.

## Goals

- Add a visually lightweight 52-week Profile preview to Overview.
- Preserve the current KPI and two-chart hierarchy and dimensions.
- Make the complete Stats → Profile view discoverable through one clear link.
- Reuse the existing background `/api/stats` warm request rather than add another request.
- Keep Overview's selected date-range semantics visibly separate from the Profile preview's fixed 52-week window.

## Non-goals

- Weekly or Cumulative controls on Overview.
- The full five-metric Profile summary on Overview.
- Replacing or resizing the existing Overview charts.
- Making the whole preview card an ambiguous nested interactive target.
- Changing Profile calculations, date windows, heat levels, tooltips, or backend APIs.
- Implementing the separately planned Last Week preset.

## Placement and Visual Hierarchy

The Overview order becomes:

1. Existing five selected-range KPI cards.
2. Existing Usage by Tool and Top Models by Cost charts.
3. New Profile activity band.
4. Existing Tools, Apps & Models, and Combined Models tables.

On wide screens, the band is a two-column surface with a 128 px minimum height; its natural height may increase for localized text but must not be fixed or clipped:

- The left column contains `Profile activity`, `Your year in tokens`, `Past 52 weeks · Daily`, and a `View full profile` link.
- The right column contains three compact metrics followed by the 52×7 Daily heatmap.
- The surface uses a subtle theme-derived tint and border. It must remain quieter than the KPI values and chart canvases.

The preview does not repeat Total Tokens because the Overview KPI represents the selected date range while Profile represents a fixed 52-week window. The three preview metrics are:

- Active days.
- Current streak.
- Longest streak.

These metrics communicate activity rather than duplicate selected-range consumption totals.

## Responsive Behavior

- At wide desktop widths, copy and activity content sit side by side.
- At narrower desktop and tablet widths, they stack inside the same surface.
- The heatmap keeps the existing square daily cells, 3 px gaps, and 2 px corner radius. When 52 columns do not fit, the heatmap scrolls horizontally to its most recent edge rather than shrinking into illegible dots.
- Mobile does not add mode controls or extra metrics.

## Components and Boundaries

### Overview Profile Shell

New namespaced markup under `overview-profile-*` owns the preview surface, loading state, metrics, heatmap scroller, and link. It does not reuse Profile view IDs, preventing duplicate IDs and cross-view selector conflicts.

### Shared Profile Calculations

The preview reuses the existing pure Profile functions:

- `getProfileActivityWindow(...)` for the 52-week Daily window.
- `summarizeProfileActivity(...)` for the three metrics.
- `buildProfileActivityCells('daily', ...)` for Daily heat levels.
- `formatProfileDayTooltip(...)` for accessible tooltip content.

The preview gets a separate renderer because its DOM, metrics, and density differ from the complete Profile view. No Profile calculation is forked or reimplemented.

### Tooltip

Daily cells use the existing structured, colored tooltip model and safe DOM renderer. Overview gets a separate namespaced tooltip element and must not rely on the hidden Stats tooltip's layout. Hover and keyboard focus both show the tooltip, and each cell retains the accessible text label.

### Navigation

`View full profile` activates the Stats top-level tab and selects the Profile sub-view. The operation preserves the existing Month and Year cursors. It does not change the selected Daily, Weekly, or Cumulative mode in the complete Profile view.

## Data Flow and Performance

Overview continues to render its primary content from `/api/usage` immediately.

The existing `scheduleStatsWarm()` path already fetches `/api/stats` after the Overview request settles. Its successful response will now:

1. Normalize `data.contributions` with the existing missing-day helper.
2. Cache those contributions for the Profile preview.
3. Render the preview only when Overview is active.

Re-entering Overview calls the preview renderer with the cached contributions. No new endpoint or additional network request is introduced. The complete Stats tab keeps its current load and refresh behavior; populating the Overview preview must not set `statsLoaded` or imply that the full Stats DOM has been hydrated.

The preview shell reserves its final space while the warm request is pending, preventing a large layout shift. Its loading treatment is low contrast and does not block the rest of Overview.

## Loading and Error States

- Pending: show the fixed-height shell with subtle metric and heatmap skeletons.
- Success: replace the skeletons with metrics and interactive Daily cells.
- Empty contributions: render zero metrics and an empty 52×7 grid; retain the link to the full Profile view.
- Warm-request failure: keep a compact unavailable state and the full-Profile link. Overview KPIs, charts, tables, and refresh behavior remain unaffected.
- A later successful Stats load or warm retry may populate the preview from cached contributions.

## Localization and Themes

All visible copy receives English and Simplified Chinese localization keys. Colors come only from existing theme tokens and Profile heat colors; there are no hard-coded light-only values. The band and tooltip must remain legible across light/dark mode and all existing style themes.

## Accessibility

- The preview is a labelled section with an explicit heading.
- Daily cells remain keyboard-focusable buttons with the same accessible tooltip text as the complete Profile view.
- The navigation link is the only action that changes views.
- Focus styling, reduced-motion behavior, and tooltip viewport collision handling match the complete Profile implementation.
- Loading and unavailable text remain understandable without color.

## Testing and Verification

Automated coverage will verify:

- Namespaced Overview markup and bilingual localization keys.
- Exactly 364 Daily cells with unchanged square-cell geometry.
- Reuse of the existing Profile activity and tooltip calculations.
- Rendering from the scheduled Stats warm response without adding a second stats fetch.
- Empty and failed warm-response behavior.
- `View full profile` routing to Stats → Profile while preserving calendar cursors and Profile mode.
- Responsive overflow and reduced-motion CSS contracts.
- Existing Profile frontend tests remain unchanged and passing.

Local browser verification will cover:

- Overview hierarchy and dimensions before and after the addition.
- Light/dark mode and English/Chinese.
- Daily hover/focus tooltips near viewport edges.
- Wide desktop, narrower desktop, and mobile layouts.
- Navigation into Profile and back to Overview.
- No unexpected chart resize, page-width overflow, or duplicate element IDs.

Relevant tests, the repository's configured lint/type checks if any, and the full test suite will run before handoff.

## Functional Impact and Regression Risks

The intended behavior change is limited to a new secondary Overview surface and a navigation link. `/api/usage`, `/api/stats`, existing Profile calculations, selected-range controls, charts, tables, and backend responses remain compatible.

Primary risks are:

- delaying or janking Overview by doing Profile work too early;
- confusing selected-range KPIs with the fixed 52-week preview;
- duplicate DOM IDs or tooltip ownership conflicts;
- shrinking the Daily cells on small screens;
- rerendering a hidden or inactive Overview after the warm response.

The placement, explicit `Past 52 weeks` label, namespaced DOM, scheduled warm-response reuse, active-tab guard, and regression tests address these risks.
