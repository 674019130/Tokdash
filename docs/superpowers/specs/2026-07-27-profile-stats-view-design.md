# Profile Stats View Design

## Status

Approved for local implementation on 2026-07-27. This document covers the first pull request proposed in [Issue #10](https://github.com/JingbiaoMei/Tokdash/issues/10). The separate **Last Week** quick-range preset will use its own branch, design, and pull request.

## Context

Tokdash already exposes a detailed Stats tab with Month, Year, and 3D calendar views. Issue #10 proposes an optional Codex Profile-inspired overview that is compact and personal while preserving the existing detailed views.

The first implementation will be frontend-only. It will reuse the daily contribution rows already returned by `GET /api/stats`; it will not add an endpoint, reparse source logs, or load the Sessions APIs.

## Goals

- Add a Profile sub-view inside the existing Stats tab.
- Present five reliable summary metrics for a 52-week visible window.
- Add Daily, Weekly, and Cumulative activity modes derived from the same daily contribution data.
- Match the approved compact calendar treatment: 52 columns, seven square day cells per column, 3 px gaps, 2 px cell corners, and a 732 px desktop width cap.
- Preserve Tokdash themes, localization, loading behavior, and all existing Stats views.

## Non-goals

- Share-card generation, image download, or clipboard support.
- Activity-insight or most-used-tool/model panels.
- Tool, provider, or model filters.
- User accounts, public profiles, editable avatars, or usernames.
- A fabricated longest-task metric when no reliable duration is present in `/api/stats`.
- Backend or database changes.

## Placement and Navigation

`Profile` will be added as a fourth Stats sub-view alongside `Month`, `Year`, and `3D`.

- `Month` remains the default so existing users see no navigation change on load.
- Selecting `Profile` changes only `calendarState.view`; it does not reset the current Month or Year cursor.
- Returning to Month, Year, or 3D restores the existing view state.
- The new Profile markup and styles will be namespaced under `profile-activity-*` to avoid changing existing calendar selectors.

The Profile view contains:

1. A five-column summary strip.
2. A `Token activity` header with Daily, Weekly, and Cumulative controls.
3. A 52-by-7 activity grid and month labels.

It does not duplicate account or profile-management UI from Codex.

## Data Source and Window

The view uses `statsCache.default`, populated by the existing initial `/api/stats` request. No additional fetch is made when switching Profile activity modes.

The display window is calendar-aligned:

- Find the Monday containing the current local date.
- Move back 51 weeks to obtain the first displayed Monday.
- Render 52 Monday-to-Sunday columns.
- Treat dates after today as future cells: visually empty, excluded from metrics, and without usage tooltips.
- Fill missing historical dates with the existing empty-contribution shape.

The default `/api/stats` response covers 365 days, which is sufficient for this 52-week aligned window, including the partial current week.

## Summary Metrics

All summary values are calculated from non-future cells in the visible 52-week window.

1. **Recorded tokens**: sum of `day.totals.tokens`.
2. **Peak day**: highest daily token count, with the date available in supporting text or tooltip.
3. **Active days**: number of days with token usage greater than zero.
4. **Current streak**: consecutive active days counted backward from today; zero when today is inactive.
5. **Longest streak**: longest consecutive sequence of active days in the visible window.

The UI will not use “Lifetime tokens,” because local logs may have been deleted and `/api/stats` is a bounded history response. `Active days` replaces the visual reference's `Longest task`, which cannot be calculated reliably from this endpoint.

## Activity Derivation

All three modes retain the same 52-by-7 day-cell geometry. This keeps tab changes visually stable and makes Weekly and Cumulative views directly comparable with Daily.

### Daily

- One cell represents one calendar day.
- Zero usage uses the empty-cell color.
- Positive usage is normalized against the peak daily token count in the visible window.
- Four bands are used:
  - level 1: greater than zero through 25% of the peak;
  - level 2: greater than 25% through 50%;
  - level 3: greater than 50% through 75%;
  - level 4: greater than 75%.
- The four colors are sampled from the active Tokdash heatmap palette, preserving light, dark, and custom theme behavior.

### Weekly

- Each Monday-to-Sunday column is summed into one weekly total.
- A positive week fills at least one square.
- Filled height is `ceil(weekTokens / peakWeekTokens * 7)`, clamped to 1-7.
- Filled squares start at the bottom of the column and use a single strong theme color.
- Hovering any part of the column highlights that week's filled cells and opens one weekly tooltip.

### Cumulative

- Weekly totals are converted to prefix sums.
- Filled height is `ceil(cumulativeTokens / finalCumulativeTokens * 7)`, clamped to 1-7 for positive values.
- Filled squares start at the bottom, producing a non-decreasing staircase.
- Hovering a column reports the recorded total through that week.

## Tooltips

Daily tooltips show the date and the contribution fields already available locally:

- total tokens;
- input and output tokens;
- cache-read and cache-write tokens;
- reasoning tokens when non-zero;
- estimated cost, explicitly labelled as estimated.

Weekly tooltips aggregate the same fields over the Monday-to-Sunday range. Cumulative tooltips aggregate them from the first displayed Monday through the hovered week. Missing optional fields are omitted rather than inferred.

## Component and Function Boundaries

Tokdash currently ships the frontend as `src/tokdash/static/index.html`, so this PR will follow the existing architecture without introducing a bundler or framework.

The implementation should keep calculation and rendering separate through focused functions:

- `getProfileActivityWindow(contributions, today)` normalizes the 52-week daily array.
- `summarizeProfileActivity(days, today)` calculates the five summary metrics.
- `groupProfileActivityWeeks(days)` builds Monday-to-Sunday aggregate objects, including token breakdown and cost.
- `buildProfileActivityCells(mode, days, weeks)` returns display levels without manipulating the DOM.
- `renderProfileSummary(summary)` updates the metric strip.
- `renderProfileActivity(mode)` renders cells, labels, and tooltip targets.
- `setProfileActivityMode(mode)` changes Daily, Weekly, or Cumulative without a network request.

Profile-specific state is limited to the selected activity mode. The existing `calendarState` remains the source of truth for the Stats sub-view and existing calendar cursors.

## Responsive and Accessible Behavior

- Desktop content is capped at 732 CSS px.
- The 52 columns divide the available desktop width evenly, with square cells and 3 px gaps.
- On narrow screens, the grid keeps legible square cells inside a horizontal scroller rather than collapsing into tiny dots.
- The scroller initially reveals the newest weeks.
- Daily, Weekly, and Cumulative controls are semantic buttons with `aria-pressed` state.
- The grid has an accessible summary label. Tooltip targets also expose equivalent `aria-label` text.
- Tooltips open on pointer hover and keyboard focus.
- Motion is limited to the existing lightweight color transitions and respects reduced-motion preferences.

## Loading, Empty, and Error States

- Before the first `/api/stats` response, Profile uses the existing Stats loading overlay.
- If the initial request fails, the existing Retry action remains the only recovery path.
- A failed background refresh keeps the last successful Profile rendering, matching current Stats behavior.
- A successful response with no activity renders five zero or em-dash metrics and an empty 52-week grid.
- Optional breakdown values that are absent are omitted from tooltips.
- Future cells remain empty and non-interactive.

## Localization

New labels and tooltip templates will be added to the existing English and Simplified Chinese dictionaries. No visible label will be hard-coded in a render function. Date and number formatting will reuse existing helpers where possible.

## Testing and Verification

### Automated tests

Add focused frontend tests following the repository's existing Node-from-pytest pattern:

- Extract the pure JavaScript profile functions from the shipped `index.html`.
- Execute them with Node when Node is available; skip consistently with existing frontend tests otherwise.
- Cover:
  - exactly 52 columns and 364 cells;
  - Monday-to-Sunday grouping across month and year boundaries;
  - future cells excluded from metrics;
  - daily 0-4 level thresholds;
  - positive weekly values always filling at least one cell;
  - weekly peak filling seven cells;
  - cumulative heights never decreasing;
  - current and longest streak calculations;
  - empty data and all-zero data;
  - aggregation of token breakdown and estimated cost.

Add a lightweight HTML contract assertion for the Profile sub-view IDs, activity controls, and English/Chinese localization keys.

### Repository checks

- Run the focused frontend tests first.
- Run the full pytest suite.
- Run the repository's configured lint and type checks if present.
- Because the frontend is embedded JavaScript rather than TypeScript, run a Node syntax check on the extracted script and report that no static JS type-check target exists unless the repository adds one before implementation.

### Manual verification

- Start Tokdash locally and inspect Profile in light and dark themes.
- Verify Daily, Weekly, and Cumulative rendering with real local data.
- Hover and keyboard-focus representative daily and weekly columns.
- Resize through desktop, tablet, and mobile widths.
- Switch repeatedly between Profile and Month/Year/3D to confirm their state is preserved.
- Verify the empty-data and initial-load failure states.

The user will review the running local UI before any pull request is opened.

## Compatibility and Regression Risk

The change is additive and frontend-only. Existing API payloads, persistence, pricing, source parsing, and detailed Stats views remain unchanged.

Primary regression risks are:

- accidentally broad CSS selectors changing existing calendars;
- extending view switching in a way that hides or resets Month/Year/3D;
- locale or timezone errors around Monday boundaries;
- stale Profile state after a stats refresh;
- excessive tooltip focus targets or mobile overflow.

Namespaced styles, pure data-derivation helpers, state-preservation tests, local-date test cases, and manual responsive verification mitigate these risks.

## Pull Request Boundary

This pull request includes only the Profile Stats sub-view and its tests/localization. It does not include the Last Week preset or share-card work.

After local implementation and user acceptance, the branch can be pushed and opened as a pull request linked to Issue #10. The Last Week preset will then be developed from `main` on a separate branch and submitted as a separate pull request.
