# Profile Visual Polish Design

## Status

Approved in conversation on 2026-07-27 for local implementation on the existing `feat/profile-stats-view` branch. This is a focused refinement of the Profile Stats view designed in `2026-07-27-profile-stats-view-design.md`; it does not expand the pull request's feature scope.

## Context

The Profile Stats view is functionally complete and has been verified locally in Daily, Weekly, and Cumulative modes. Its layout, calendar geometry, and data hierarchy are correct, but the current presentation is visually flat:

- all five summary values use the same text treatment;
- activity-mode controls rely mostly on text color;
- cell hover feedback is subtle;
- tooltips are rendered as one plain preformatted text block, so labels and values are difficult to scan.

The goal of this pass is a medium-strength visual emphasis: noticeably clearer than the current view while retaining Tokdash's restrained, theme-native appearance.

## Approaches Considered

### 1. Semantic highlights — selected

Use the existing theme colors to distinguish meaning: colored summary values, a tinted active control, focused heatmap hover feedback, and structured tooltip rows. This improves scanability without changing the layout.

### 2. Fully tinted statistic cards

Give every summary item its own colored background and border. This is more immediately colorful, but five adjacent tinted panels compete with the heatmap and make custom themes noisier.

### 3. Unified gradient treatment

Use one primary-to-secondary gradient across headings, controls, and tooltip surfaces. This creates a strong visual identity but provides less semantic distinction between token categories and risks resembling a share card rather than an application view.

The selected direction is semantic highlighting with restrained tinted surfaces. Gradients and large colored panels are intentionally excluded.

## Goals

- Make important values and the selected activity mode identifiable at a glance.
- Make tooltip labels, values, and token categories easy to scan.
- Add local color and depth without changing the compact calendar geometry.
- Reuse theme variables so every existing light, dark, and custom theme remains coherent.
- Preserve keyboard, pointer, localization, and reduced-motion behavior.

## Non-goals

- Changes to statistics, aggregation, date windows, or heatmap levels.
- Changes to the 52-by-7 grid, cell size, gap, corner radius, or desktop width.
- New API fields, endpoints, persistence, or backend work.
- New profile identity, share-card, animation, or visualization features.
- Strong gradients, neon glows, or full-card color fills.

## Visual Treatment

### Summary strip

The five-column structure and separators remain unchanged. Emphasis is applied primarily to values rather than whole panels:

- Recorded tokens: `--color-primary`.
- Peak day: `--color-secondary`.
- Active days: `--color-cost`.
- Current streak: `--color-cta`.
- Longest streak: `--color-primary`, visually differentiated from Recorded tokens by position and label rather than an additional palette color.

Each value receives a slightly stronger font weight and a restrained text shadow derived from its tone. The shadow must remain subtle in both light and dark themes and must not reduce contrast. Labels stay neutral so the numbers retain priority.

The strip may receive a faint primary-tinted inset highlight, but each statistic must not become an independently filled card.

### Activity heading and mode controls

`Token activity` gains a small primary accent mark beside the heading. It remains a normal section heading and does not become a banner.

Daily, Weekly, and Cumulative remain semantic buttons with `aria-pressed`. Their visual states become:

- inactive: neutral text and transparent background;
- inactive hover/focus: primary-tinted background and clearer text;
- active: primary-colored text, a soft primary-tinted pill, a theme-derived border, and a restrained inset highlight.

The controls must not move when selection changes, and their hit targets must remain at least as large as the current implementation.

### Heatmap interaction

The resting heatmap palette and all fill calculations remain unchanged. Feedback is added only to the active target:

- Daily: the hovered or keyboard-focused day gets a one-pixel theme-derived ring, a small brightness increase, and at most a one-pixel upward offset.
- Weekly and Cumulative: the existing column highlight is strengthened with the same ring/brightness language across the column's relevant cells.
- Empty aggregate cells may receive a faint primary tint while the column is targeted, but future cells remain non-interactive and unchanged.

No hover effect may alter the grid's measured width, gap, or cell dimensions. Transform-based motion must be disabled under `prefers-reduced-motion: reduce`.

## Structured Tooltip

### Layout

The tooltip changes from a plain newline-separated text block to a small structured panel:

1. A tinted header containing the day or date range.
2. A prominent Total tokens row.
3. Optional detail rows for Input, Output, Cache read, Cache write, and Reasoning.
4. An optional Estimated cost row separated from token rows.

Rows use a small colored dot, a neutral label, and a right-aligned tabular number. Total tokens is larger and uses the primary tone. Separators and surfaces are derived from the current theme border and glass colors.

The tooltip remains compact, pointer-transparent, and positioned by the existing collision-aware logic. It must stay legible at the current maximum width and may grow slightly only if needed for label/value separation.

### Semantic tones

Tooltip tones reuse the existing theme palette:

- Total tokens and Input: `--color-primary`.
- Output: `--color-secondary`.
- Cache read: `--color-cost`.
- Cache write: `--color-cta`.
- Reasoning: a theme-derived mix of primary and secondary.
- Estimated cost: `--color-cost`.

No fixed light- or dark-only colors are introduced. Background tints, rings, and shadows use `color-mix()` with existing variables, which the application already relies on.

### Data and DOM boundary

Tooltip formatting will produce a structured model instead of only a display string:

```js
{
  title,
  rows: [{ key, label, value, tone, prominent }],
  accessibleText
}
```

The renderer will create elements with `document.createElement()` and assign user-visible values through `textContent`; it will not interpolate values into `innerHTML`.

`accessibleText` preserves the same complete information as the visual panel and is assigned to the target's `aria-label`. Input, Output, Cache read, Cache write, and Estimated cost remain visible even when their value is zero, matching the current tooltip. Reasoning remains the only conditionally omitted row and is hidden when its value is zero. Daily, Weekly, and Cumulative tooltips use the same model and renderer.

## Localization and Accessibility

- Existing English and Simplified Chinese labels remain the source of tooltip copy.
- No visible English label is hard-coded into the renderer.
- Tooltip color is supplementary; labels and layout continue to communicate meaning without color.
- Existing hover and keyboard-focus triggers remain equivalent.
- Focus-visible styling must be at least as clear as pointer hover styling.
- The tooltip retains `role="tooltip"`, and target `aria-label` text remains a complete plain-text summary.
- Text and tinted surfaces must preserve readable contrast across all bundled themes.

## Component Boundaries

The work remains inside the existing embedded frontend architecture in `src/tokdash/static/index.html`:

- add namespaced Profile polish styles;
- add semantic classes or data attributes to summary values;
- update activity-mode button states without changing their event flow;
- replace the plain tooltip formatter result with a structured model;
- update the tooltip renderer to build safe DOM nodes;
- preserve current positioning, target binding, and aggregation helpers.

No framework, dependency, asset, or bundler is added.

## Testing and Verification

### Automated checks

Focused tests should cover:

- summary values expose the intended semantic tone hooks;
- activity controls retain `aria-pressed` and active-state hooks;
- tooltip models contain title, ordered rows, tones, and complete `accessibleText`;
- Input, Output, Cache read, Cache write, and Estimated cost retain zero-value rows while zero Reasoning remains omitted;
- Daily, Weekly, and Cumulative models render the appropriate date title and totals;
- the renderer uses structured nodes rather than a preformatted text blob;
- the shipped script remains syntactically valid.

Run the relevant focused pytest tests, the repository's full pytest suite, and the available type/static checks. If the repository still has no configured JavaScript type checker, report that explicitly rather than substituting an unrelated tool.

### Manual checks

- Inspect English and Simplified Chinese in light and dark themes.
- Verify all bundled/custom theme palettes remain coherent.
- Hover and keyboard-focus Daily cells and Weekly/Cumulative columns.
- Confirm tooltip hierarchy, alignment, optional rows, and viewport collision handling.
- Verify the grid remains 52 by 7 with the existing square size, three-pixel gaps, two-pixel corners, and desktop width.
- Verify reduced-motion behavior and narrow-screen horizontal scrolling.
- Switch among Profile, Month, Year, and 3D to confirm no existing state changes.

The user will review the running local UI before any push or pull request.

## Functional Impact and Regression Risk

The intended behavior change is visual only: clearer semantic emphasis and a structured tooltip presentation. Statistics, aggregation, navigation, data loading, and accessible content remain compatible with the previous implementation.

Primary risks are:

- theme combinations producing insufficient contrast;
- a larger tooltip overflowing narrow viewports;
- DOM refactoring accidentally omitting an accessible label or optional metric;
- hover transforms visually disturbing the tight grid;
- broad selectors affecting Month, Year, or 3D views.

Namespaced selectors, theme-derived colors, safe DOM construction, focused contract tests, and manual theme/responsive checks mitigate these risks.

## Pull Request Boundary

This polish is part of the existing Profile Stats pull request and branch. It does not include the separately planned Last Week range preset or any share-card/profile publishing work.
