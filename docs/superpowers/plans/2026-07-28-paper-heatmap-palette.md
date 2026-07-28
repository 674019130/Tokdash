# Paper Heatmap and Milestone Palette Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the approved Slate Ink heat scale and Mineral Spectrum milestone palette to the Paper theme without changing calculations, data contracts, or any other theme.

**Architecture:** Keep base heat colors in the existing JavaScript theme configuration so Month, Year, 3D, Profile, and legends update through the shared `HEAT_COLORS` path. Add Paper-only Light/Dark milestone CSS variables in `themes.css`, retain the existing milestone defaults as the non-Paper fallback, and add a transparent-by-default semantic keyline to the existing aura geometry.

**Tech Stack:** HTML/CSS, vanilla browser JavaScript, Python 3.10+ pytest contract tests, Node.js syntax validation, existing FastAPI/Uvicorn local server.

## Global Constraints

- Implement only `docs/superpowers/specs/2026-07-28-paper-heatmap-palette-design.md`.
- Stay on the current normal branch `feat/profile-stats-view`; do not create a linked worktree.
- Never delete files. Do not stage or commit `.superpowers/` visual-companion artifacts.
- Change only the Paper theme's base heat palette and Profile milestone palette. Keep all nine non-Paper themes unchanged.
- Use the exact approved Slate Ink and Mineral Spectrum Light/Dark colors from the design spec.
- Preserve the existing Daily relative-level thresholds, Month/Year/3D quantiles, Weekly/Cumulative height encoding, 52-week window, milestone thresholds, labels, tooltip data, cell geometry, 3 px gaps, and 2 px Profile radius.
- Keep milestone defaults cyan/violet/amber/pink for non-Paper themes.
- Add the milestone keyline through `--profile-milestone-keyline`; its default must be transparent and Paper must use `var(--color-bg)`.
- Do not add requests, persistence, state, DOM attributes, backend fields, dependencies, configuration, or animation.
- Before handoff, run focused tests, the exact compile command, the full suite, JavaScript syntax validation through the existing frontend test, and configured type-check/lint discovery.
- Call out the intentional compatibility impact: every Paper Month, Year, 3D, Profile, and associated legend changes color; data and non-Paper behavior do not change.
- Keep all work local until the user reviews it. Do not push or open a PR.

## File Map

- Modify: `src/tokdash/static/theme-config.js`
  - Owns the eight-entry Paper Light/Dark base heat palettes consumed through `HEAT_COLORS`.
- Modify: `src/tokdash/static/themes.css`
  - Owns Paper Light/Dark overrides for the four milestone colors and the Paper keyline color.
- Modify: `src/tokdash/static/index.html`
  - Owns default milestone variables and existing tier ring/glow geometry; gains the transparent keyline in each milestone shadow stack.
- Modify: `tests/test_profile_stats_frontend.py`
  - Owns exact palette, five-level Profile mapping, theme scoping, fallback, and keyline contracts.
- Reference only: `docs/superpowers/specs/2026-07-28-paper-heatmap-palette-design.md`
  - Approved colors, scope, behavior, compatibility, and verification criteria.

---

### Task 1: Replace the Paper Base Heat Scale with Slate Ink

**Files:**
- Modify: `tests/test_profile_stats_frontend.py:10-15, 620-650`
- Modify: `src/tokdash/static/theme-config.js:24-27`

**Interfaces:**
- Consumes: `window.TOKDASH_THEME_CONFIG.heatColorsMap`, the existing `HEAT_COLORS` theme-selection path, and `getProfileActivityColor(level)`.
- Produces: exact eight-color Paper Light/Dark arrays. Profile levels 0–4 continue mapping to indices `[0, 2, 4, 5, 7]`; Month, Year, and 3D continue consuming all eight colors.

- [ ] **Step 1: Add a failing exact-palette contract test**

Add next to `INDEX_HTML`:

```python
THEME_CONFIG_JS = Path(tokdash.__file__).parent / "static" / "theme-config.js"


def _heat_palette_for(theme: str) -> tuple[list[str], list[str]]:
    source = THEME_CONFIG_JS.read_text(encoding="utf-8")
    heat_source = source[source.index("heatColorsMap:") : source.index("chartPaletteMap:")]
    match = re.search(
        rf"{re.escape(theme)}:\s*\{{\s*light:\s*(\[[^\]]+\]),\s*dark:\s*(\[[^\]]+\])",
        heat_source,
    )
    assert match, f"heat palette not found for {theme}"
    return json.loads(match.group(1)), json.loads(match.group(2))
```

Add after `test_profile_activity_legend_is_safe_localized_and_mode_aware`:

```python
def test_paper_uses_approved_slate_ink_heat_palette():
    light, dark = _heat_palette_for("paper")
    assert light == [
        "#F3EFE8", "#E8E7E4", "#DCE0E2", "#C8D0D4",
        "#B4BEC4", "#778995", "#5D7180", "#42596A",
    ]
    assert dark == [
        "#191716", "#222629", "#2B3034", "#384148",
        "#4C5A64", "#8399A7", "#A6BAC4", "#CDDCE3",
    ]

    profile_indices = [round((level / 4) * (len(light) - 1)) for level in range(5)]
    assert profile_indices == [0, 2, 4, 5, 7]
    assert [light[index] for index in profile_indices] == [
        "#F3EFE8", "#DCE0E2", "#B4BEC4", "#778995", "#42596A",
    ]
    assert [dark[index] for index in profile_indices] == [
        "#191716", "#2B3034", "#4C5A64", "#8399A7", "#CDDCE3",
    ]

    classic_light, classic_dark = _heat_palette_for("classic")
    assert classic_light == [
        "#EEF2F7", "#E0E7FF", "#C7D2FE", "#A5B4FC",
        "#60A5FA", "#3B82F6", "#2563EB", "#1E40AF",
    ]
    assert classic_dark == [
        "#172033", "#1E293B", "#1D4ED8", "#2563EB",
        "#3B82F6", "#60A5FA", "#93C5FD", "#BFDBFE",
    ]

    activity_color = _extract_js_function(
        INDEX_HTML.read_text(encoding="utf-8"),
        "function getProfileActivityColor(level) {",
    )
    assert "Math.round((safeLevel / 4) * Math.max(0, HEAT_COLORS.length - 1))" in activity_color
```

- [ ] **Step 2: Run the new test and verify the intended failure**

Run:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest \
  tests/test_profile_stats_frontend.py::test_paper_uses_approved_slate_ink_heat_palette -q
```

Expected: FAIL because Paper still contains the old beige/brown heat arrays. The Classic assertions should already pass.

- [ ] **Step 3: Replace only the Paper heat arrays**

Replace `heatColorsMap.paper` in `src/tokdash/static/theme-config.js` with:

```javascript
paper: {
  light: ["#F3EFE8", "#E8E7E4", "#DCE0E2", "#C8D0D4", "#B4BEC4", "#778995", "#5D7180", "#42596A"],
  dark: ["#191716", "#222629", "#2B3034", "#384148", "#4C5A64", "#8399A7", "#A6BAC4", "#CDDCE3"],
},
```

Do not change `chartPaletteMap.paper`, any other `heatColorsMap` entry, or `getProfileActivityColor`.

- [ ] **Step 4: Run the palette and existing Profile level tests**

Run:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest \
  tests/test_profile_stats_frontend.py::test_paper_uses_approved_slate_ink_heat_palette \
  tests/test_profile_stats_frontend.py::test_profile_week_and_cumulative_cells_follow_seven_level_scale \
  tests/test_profile_stats_frontend.py::test_profile_activity_legend_is_safe_localized_and_mode_aware -q
```

Expected: all three tests PASS. Daily thresholds and aggregate height behavior remain unchanged.

- [ ] **Step 5: Commit the Slate Ink base palette**

```bash
git add src/tokdash/static/theme-config.js tests/test_profile_stats_frontend.py
git commit -m "style: refresh Paper heatmap palette"
```

---

### Task 2: Add Paper Mineral Spectrum Milestones and the Keyline

**Files:**
- Modify: `tests/test_profile_stats_frontend.py:10-16, 530-555`
- Modify: `src/tokdash/static/themes.css:120-320`
- Modify: `src/tokdash/static/index.html:491-511`

**Interfaces:**
- Consumes: existing `--profile-milestone-1..4`, `[data-milestone]`, `[data-tone="milestone-N"]`, tooltip badges, legend badges, and Overview/Profile tier-specific shadow geometry.
- Produces: Paper-only Mineral Spectrum Light/Dark variable overrides and `--profile-milestone-keyline`. Non-Paper surfaces keep the existing milestone values because the default keyline is transparent.

- [ ] **Step 1: Add a failing theme-scoping and keyline contract test**

Add next to the other static paths:

```python
THEMES_CSS = Path(tokdash.__file__).parent / "static" / "themes.css"
```

Add after `test_profile_milestone_tooltip_and_tier_aura_contract`:

```python
def test_paper_uses_mineral_spectrum_milestones_and_keyline():
    source = INDEX_HTML.read_text(encoding="utf-8")
    compact = re.sub(r"\s+", "", source)
    themes = THEMES_CSS.read_text(encoding="utf-8")

    light_rule = """
html[data-ui-theme="paper"] .profile-activity-shell,
html[data-ui-theme="paper"] .overview-profile-band {
  --profile-milestone-1: #3E8C78;
  --profile-milestone-2: #557AA2;
  --profile-milestone-3: #C18A35;
  --profile-milestone-4: #B85466;
  --profile-milestone-keyline: var(--color-bg);
}
""".strip()
    dark_rule = """
html.dark[data-ui-theme="paper"] .profile-activity-shell,
html.dark[data-ui-theme="paper"] .overview-profile-band {
  --profile-milestone-1: #75C2AC;
  --profile-milestone-2: #8FB1D4;
  --profile-milestone-3: #E2B458;
  --profile-milestone-4: #EA8798;
  --profile-milestone-keyline: var(--color-bg);
}
""".strip()

    assert light_rule in themes
    assert dark_rule in themes
    assert "--profile-milestone-keyline:transparent;" in compact
    assert compact.count(
        "inset0001pxvar(--profile-milestone-keyline)"
    ) >= 8

    assert "--profile-milestone-1:#06b6d4;" in compact
    assert "--profile-milestone-2:#8b5cf6;" in compact
    assert "--profile-milestone-3:#f59e0b;" in compact
    assert "--profile-milestone-4:#ec4899;" in compact
```

- [ ] **Step 2: Run the new test and verify the intended failure**

Run:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest \
  tests/test_profile_stats_frontend.py::test_paper_uses_mineral_spectrum_milestones_and_keyline -q
```

Expected: FAIL because Paper-specific milestone rules and the keyline variable do not exist.

- [ ] **Step 3: Add the Paper Light and Dark milestone variables**

In `src/tokdash/static/themes.css`, add the Light rule after the base Paper token block and the Dark rule after the dark Paper token block:

```css
html[data-ui-theme="paper"] .profile-activity-shell,
html[data-ui-theme="paper"] .overview-profile-band {
  --profile-milestone-1: #3E8C78;
  --profile-milestone-2: #557AA2;
  --profile-milestone-3: #C18A35;
  --profile-milestone-4: #B85466;
  --profile-milestone-keyline: var(--color-bg);
}

html.dark[data-ui-theme="paper"] .profile-activity-shell,
html.dark[data-ui-theme="paper"] .overview-profile-band {
  --profile-milestone-1: #75C2AC;
  --profile-milestone-2: #8FB1D4;
  --profile-milestone-3: #E2B458;
  --profile-milestone-4: #EA8798;
  --profile-milestone-keyline: var(--color-bg);
}
```

Do not replace the generic Profile milestone values in `index.html`; they remain the fallback for all non-Paper themes.

- [ ] **Step 4: Add the transparent default and inset keyline to every milestone shadow stack**

Extend the shared variables:

```css
.profile-activity-shell,.overview-profile-band{--profile-milestone-1:#06b6d4;--profile-milestone-2:#8b5cf6;--profile-milestone-3:#f59e0b;--profile-milestone-4:#ec4899;--profile-milestone-keyline:transparent;}
```

Replace the milestone cell, hover, and compact Overview shadow rules with:

```css
.profile-activity-cell[data-milestone="1"]{box-shadow:inset 0 0 0 1px var(--profile-milestone-keyline),0 0 0 1px color-mix(in srgb,var(--profile-milestone-tone) 66%,transparent);}
.profile-activity-cell[data-milestone="2"]{box-shadow:inset 0 0 0 1px var(--profile-milestone-keyline),0 0 0 1px color-mix(in srgb,var(--profile-milestone-tone) 72%,transparent),0 0 7px color-mix(in srgb,var(--profile-milestone-tone) 34%,transparent);}
.profile-activity-cell[data-milestone="3"]{box-shadow:inset 0 0 0 1px var(--profile-milestone-keyline),0 0 0 1px color-mix(in srgb,var(--profile-milestone-tone) 82%,transparent),0 0 0 2px color-mix(in srgb,var(--profile-milestone-tone) 22%,transparent),0 0 10px color-mix(in srgb,var(--profile-milestone-tone) 44%,transparent);}
.profile-activity-cell[data-milestone="4"]{box-shadow:inset 0 0 0 1px var(--profile-milestone-keyline),0 0 0 1px color-mix(in srgb,var(--color-text) 74%,transparent),0 0 0 3px color-mix(in srgb,var(--profile-milestone-tone) 38%,transparent),0 0 14px color-mix(in srgb,var(--profile-milestone-tone) 58%,transparent);}
button.profile-activity-cell[data-milestone]:not(:disabled):is(:hover,:focus-visible),.profile-activity-cell[data-milestone].is-column-hover{box-shadow:inset 0 0 0 1px var(--profile-milestone-keyline),0 0 0 1px color-mix(in srgb,var(--color-text) 82%,transparent),0 0 0 3px color-mix(in srgb,var(--profile-milestone-tone) 48%,transparent),0 0 18px color-mix(in srgb,var(--profile-milestone-tone) 68%,transparent);}
.overview-profile-cell[data-milestone="2"]{box-shadow:inset 0 0 0 1px var(--profile-milestone-keyline),0 0 0 1px color-mix(in srgb,var(--profile-milestone-tone) 66%,transparent),0 0 5px color-mix(in srgb,var(--profile-milestone-tone) 22%,transparent);}
.overview-profile-cell[data-milestone="3"]{box-shadow:inset 0 0 0 1px var(--profile-milestone-keyline),0 0 0 1px color-mix(in srgb,var(--profile-milestone-tone) 76%,transparent),0 0 0 2px color-mix(in srgb,var(--profile-milestone-tone) 18%,transparent),0 0 7px color-mix(in srgb,var(--profile-milestone-tone) 30%,transparent);}
.overview-profile-cell[data-milestone="4"]{box-shadow:inset 0 0 0 1px var(--profile-milestone-keyline),0 0 0 1px color-mix(in srgb,var(--color-text) 68%,transparent),0 0 0 2px color-mix(in srgb,var(--profile-milestone-tone) 30%,transparent),0 0 9px color-mix(in srgb,var(--profile-milestone-tone) 42%,transparent);}
```

Do not change tooltip, legend, threshold, reduced-motion, or aggregate-hit-target logic; those already consume the semantic milestone variables.

- [ ] **Step 5: Run milestone, tooltip, legend, and syntax contracts**

Run:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest \
  tests/test_profile_stats_frontend.py::test_paper_uses_mineral_spectrum_milestones_and_keyline \
  tests/test_profile_stats_frontend.py::test_profile_milestone_tooltip_and_tier_aura_contract \
  tests/test_profile_stats_frontend.py::test_profile_activity_legend_is_safe_localized_and_mode_aware \
  tests/test_profile_stats_frontend.py::test_main_inline_script_parses_with_node -q
```

Expected: all four tests PASS. The existing cyan/violet/amber/pink fallback assertions still pass.

- [ ] **Step 6: Commit the Paper milestone treatment**

```bash
git add src/tokdash/static/themes.css src/tokdash/static/index.html tests/test_profile_stats_frontend.py
git commit -m "style: align Paper milestone aura"
```

---

### Task 3: Regression, Type-Check Discovery, and Local Visual Verification

**Files:**
- Modify only if a verified defect is found: `src/tokdash/static/theme-config.js`, `src/tokdash/static/themes.css`, `src/tokdash/static/index.html`, `tests/test_profile_stats_frontend.py`

**Interfaces:**
- Consumes: Tasks 1 and 2.
- Produces: exact automated results, browser evidence across every Paper heatmap, non-Paper compatibility evidence, and a local build ready for user approval before any push or PR.

- [ ] **Step 1: Run the complete focused frontend file**

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest tests/test_profile_stats_frontend.py -q
```

Expected: every Profile frontend test PASS, including `test_main_inline_script_parses_with_node`.

- [ ] **Step 2: Run the repository's CI compile command**

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt \
  python -m compileall -q \
  src/tokdash main.py docs/guides/agents/openclaw_reporting/openclaw_cron_job.py
```

Expected: exit 0 with no diagnostics.

- [ ] **Step 3: Run the full pytest suite**

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest -q
```

Expected: PASS. If the unrelated calendar-month timezone baseline failure remains, report `tests/test_period_semantics.py::test_previous_period_range_month_uses_full_previous_calendar_month` with its exact traceback and confirm the focused frontend file passes.

- [ ] **Step 4: Perform the required type-check and lint discovery**

```bash
rg -n "\[tool\.(ruff|mypy|pyright)|ruff|mypy|pyright|eslint|typecheck|lint" \
  pyproject.toml requirements-dev.txt .github 2>/dev/null || true
```

Expected for the current repository: no configured Python/JavaScript static type-check or lint target. Report the exact command and output; do not call `compileall` or `node --check` a type checker.

- [ ] **Step 5: Confirm the existing local review server**

Run:

```bash
curl -fsS http://127.0.0.1:55424/health
```

Expected: HTTP 200. If it is not running, start it in a persistent terminal with:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt \
  tokdash serve --bind 127.0.0.1 --port 55424 --no-open
```

- [ ] **Step 6: Verify Paper and the non-Paper fallback in the local browser**

At `http://127.0.0.1:55424/`, verify:

1. Paper Light and Dark Profile Daily each show five distinguishable Slate Ink levels matching heat indices 0, 2, 4, 5, and 7.
2. Paper Weekly and Cumulative retain height encoding, strongest-color active cells, empty-color inactive cells, aligned column hit targets, and synchronized Overview/Profile controls.
3. Overview uses the same Mineral Spectrum hues with its existing quieter aura.
4. Month and Year use all eight Slate Ink colors and their legends match the cells.
5. 3D uses the same eight cube colors and legend without changing cube geometry, height, background, or interaction.
6. 100M jade, 300M sapphire, 500M amber, and 1B garnet remain visible on light, middle, and dark heat cells in resting, hover, and focus states.
7. Tooltip badges, prominent token rows, and legend badges match the milestone cell hue in both Paper modes.
8. The Paper-colored keyline separates aura from the fill without making the square appear smaller.
9. Switching Paper Light ↔ Paper Dark updates heat, milestone, tooltip, and legend colors without a reload.
10. Switching to Classic restores the unchanged Classic heat palette and cyan/violet/amber/pink milestones.
11. At approximately 795 px and a wide viewport, there is no document-level horizontal overflow and the right-edge tooltip remains inside the viewport.

- [ ] **Step 7: Inspect the final implementation scope**

Run:

```bash
git diff --check 2768111..HEAD
git status --short
git log -6 --oneline --decorate
```

Expected: no whitespace errors; tracked changes are limited to the approved plan, palette source, theme CSS, Profile CSS, and frontend tests. `.superpowers/` remains untracked and unstaged.

- [ ] **Step 8: Hand off locally before PR creation**

Report:

- the local review URL;
- focused, compile, full-suite, syntax, type-check/lint discovery, and browser results;
- any unchanged baseline failure with exact diagnostics;
- the intentional Paper-wide visual change and non-Paper compatibility result;
- that no API, calculation, threshold, data, persistence, or geometry behavior changed;
- that nothing was pushed and no PR was created pending user approval.
