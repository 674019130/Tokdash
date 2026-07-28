# Profile Activity Grid Spacing Design

## Goal

Give milestone auras slightly more visual breathing room without changing the GitHub-like square-day geometry, activity semantics, or milestone behavior.

## Decision

Increase the activity-grid gap from `3px` to `3.5px` in both the full Profile and the compact Overview embedding.

This is the midpoint between leaving the current dense layout unchanged and using a `4px` gap. Across 52 columns, `3.5px` adds about `25.5px` of inter-cell spacing compared with `3px`, while `4px` would add about `51px`.

## Geometry

Keep these properties unchanged:

- 52 columns by 7 rows.
- Square day cells.
- `2px` cell corner radius.
- Minimum cell size of `8px`.
- Profile aura reserve of `26px` plus an `8px` edge-safety gutter.
- Overview aura reserve of `16px` plus an `8px` edge-safety gutter.

Update all activity-grid gaps together:

- `.profile-activity-grid`
- `.profile-activity-week-hits`
- `.overview-profile-grid`
- `.overview-profile-week-hits`

Raise the shared minimum content width from `572px` to `595px`. The new minimum follows the grid calculation: 52 cells at `8px` plus 51 gaps at `3.5px`, rounded up to a whole CSS pixel.

The following elements must use the same `595px` minimum so that labels, overlays, and legends remain aligned:

- `.profile-activity-grid-wrap`
- `.profile-activity-months`
- `.profile-activity-legend`
- `.overview-profile-grid-wrap`

## Scope

This is a layout-only adjustment. It does not change:

- Paper Light or Paper Dark colors.
- Classic, Liquid, or Terminal heat colors.
- Milestone thresholds, tones, rings, or aura radii.
- Daily, Weekly, or Cumulative aggregation.
- Tooltip content or behavior.
- DOM structure, API responses, or persisted data.

## Responsive Behavior

At common desktop widths, the grid remains fully visible. On narrow viewports, the activity scroller may begin horizontal scrolling about `23px` earlier than before. This is an accepted trade-off to preserve square cells at the `8px` minimum and retain enough room for milestone auras.

The page itself must not develop document-level horizontal overflow. Scrolling, when required, remains contained inside the Profile or Overview activity scroller.

## Verification

Automated checks must assert:

- All four grid and overlay gap rules use `3.5px`.
- All four aligned minimum-width rules use `595px`.
- Cell radius remains `2px`.
- Profile and Overview aura-reserve variables remain unchanged.
- Relevant frontend tests and the full test suite are run.
- Python compilation succeeds through the project environment.
- Any configured type-check or lint commands are discovered and run; absence of such commands is reported.

Browser verification must cover:

- Profile and Overview at the default viewport.
- Profile and Overview at `795px` wide.
- Paper Light and Paper Dark.
- Daily, Weekly, and Cumulative modes.
- Rightmost milestone auras remain fully visible.
- No document-level horizontal overflow.
- Internal horizontal scrolling remains usable where required.

## Compatibility Risks

- Narrow screens will encounter internal activity-grid scrolling slightly sooner.
- The additional half-pixel gap can produce subpixel cell widths at fluid desktop sizes; cells remain square because width and height are derived from the same grid tracks.
- Overlay and legend alignment would regress if any corresponding gap or minimum-width rule is missed, so the change must be applied and tested as one synchronized geometry update.
