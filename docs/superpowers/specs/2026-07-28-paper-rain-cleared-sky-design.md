# Paper Rain-cleared Sky Heatmap Design

## Goal

Replace the Paper theme's mismatched blue-gray heatmap and mineral milestone aura with one coherent anime-summer palette, while fixing the clipped rightmost activity cell. The selected direction is **Rain-cleared Sky**: water-blue activity cells with twilight violet, sunset orange, and peach-red milestone accents.

## Scope

This change affects only the Paper theme and the two Profile activity surfaces:

- Paper heat colors used by Month, Year, 3D, Profile, and their legends
- Paper milestone colors used by Daily, Weekly, and Cumulative Profile views
- Milestone rings and glow intensity in the full Profile and Overview embed
- End padding in the full Profile and Overview horizontal activity scrollers

Classic, Elevated, Liquid, Vibrant, Midnight, Terminal, Brutalist, Arcade, and Studio keep their existing colors and fallback milestone treatment.

## Heat Palette

### Paper Light

The eight activity levels progress from warm paper to deep water blue:

1. `#F6F2EA`
2. `#E4EFF0`
3. `#CCE4E6`
4. `#A9D4DA`
5. `#7FBCC8`
6. `#559FB2`
7. `#39798F`
8. `#27566F`

### Paper Dark

The dark variant progresses from night charcoal to luminous rain-blue:

1. `#1C2026`
2. `#223039`
3. `#293E48`
4. `#31505E`
5. `#3B6575`
6. `#4C7E8F`
7. `#6A9EAC`
8. `#9CC6CD`

The existing heat-level calculation, data normalization, and view-specific aggregation remain unchanged.

## Milestone Palette

Milestone thresholds stay at 100M, 300M, 500M, and 1B tokens.

| Tier | Paper Light | Paper Dark | Role |
| --- | --- | --- | --- |
| 100M | `#20AE9B` | `#4ED1BA` | Rain-cleared teal |
| 300M | `#796DE2` | `#9A8CFF` | Twilight violet |
| 500M | `#F28D42` | `#FFB467` | Sunset orange |
| 1B | `#E95078` | `#FF7398` | Comet peach-red |

Paper keeps an inset keyline using `var(--color-bg)` so the colored ring remains distinct from the day-cell fill. Non-Paper themes keep the transparent fallback keyline.

## Cell Geometry

The activity grid continues to use the previously approved GitHub-like geometry:

- Square day cells
- `2px` corner radius
- `3px` gap
- 52 week columns by 7 day rows

This change does not resize cells or alter the grid, month labels, legend alignment, or horizontal-scroll breakpoint.

## Aura Treatment

The four milestone tiers become visibly progressive:

- 100M: clear two-pixel colored ring with a compact glow
- 300M: stronger ring and a wider glow
- 500M: dark/text keyline, three-pixel colored outer ring, and a brighter sunset glow
- 1B: strongest text keyline, four-pixel peach-red outer ring, and the widest glow

The full Profile follows the approved visual companion strength. The Overview embed uses the same colors and hierarchy with smaller blur radii so neighboring compact cells remain legible. Hover and keyboard focus strengthen the active milestone without changing its tier color.

Weekly and Cumulative keep the existing transparent hit-target layer. Their milestone styling continues to be attached to the corresponding day column, so all modes remain aligned to the daily grid.

## Right-edge Safety Gutter

The rightmost cell is currently clipped because CSS box shadows do not contribute to `scrollWidth`; the grid content ends exactly at the final cell's border box.

Add `8px` of logical inline-end scrollable space to both:

- `.profile-activity-scroll`
- `.overview-profile-scroll`

The gutter must allow the final 1B aura to render completely when scrolled to the end. It must not add document-level horizontal overflow, change the left alignment, or shrink the grid cells.

## Accessibility and Interaction

- Existing grid roles, accessible names, tooltips, and keyboard hit targets remain unchanged.
- Color is not the sole milestone signal: the existing rings, tier labels, and tooltip badges remain.
- Paper Light and Dark must retain readable contrast for empty cells, active cells, legend labels, and milestone badges.
- Reduced-motion behavior remains unchanged.

## Compatibility and Behavior Impact

Expected behavior changes:

- Paper heatmaps and legends use the Rain-cleared Sky palette in every heatmap surface.
- Paper Profile milestones use the new anime-summer colors and stronger aura hierarchy.
- The final activity column has an 8px scrollable safety gutter and is no longer clipped.

Compatibility boundaries:

- No API, storage, date-range, token-total, aggregation, threshold, or tooltip-data changes
- No changes to non-Paper themes
- No cell-size, grid-dimension, month-label, or mode-switching changes
- The wider aura can overlap nearby cells visually by design, but must not change hit testing or layout dimensions

## Verification

Automated coverage must assert:

- Exact Paper Light and Dark eight-color heat arrays
- Exact Paper Light and Dark milestone variables
- Paper keyline and unchanged non-Paper fallback
- Stronger full Profile and scaled Overview shadow stacks
- `8px` logical inline-end gutter on both activity scrollers
- Existing Profile renderer, mode, legend, and tooltip contracts remain intact

Manual browser verification must cover:

- Paper Light and Dark
- Full Profile and Overview embed
- Daily, Weekly, and Cumulative
- Month, Year, and 3D Paper heat colors
- Last-column 1B aura at the horizontal scroll end
- Desktop and 795px viewport without document-level overflow
- Classic fallback remains unchanged
- No browser console errors
