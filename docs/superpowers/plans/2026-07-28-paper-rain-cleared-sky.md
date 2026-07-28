# Paper Rain-cleared Sky Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the Rain-cleared Sky palette to every Paper heatmap, strengthen Paper milestone auras, and keep the rightmost Profile activity cell fully visible.

**Architecture:** Keep the existing theme and Profile renderers unchanged. Replace only Paper theme tokens in `theme-config.js` and `themes.css`, then adjust the existing CSS-only milestone and scroll-container contracts in `index.html`; all data aggregation, thresholds, DOM rendering, and interaction logic continue to use the current shared paths.

**Tech Stack:** Python 3.10+, pytest, static HTML/CSS/JavaScript, Tokdash local FastAPI server, Codex in-app browser for visual verification.

## Global Constraints

- Paper Light heat colors are exactly `#F6F2EA #E4EFF0 #CCE4E6 #A9D4DA #7FBCC8 #559FB2 #39798F #27566F`.
- Paper Dark heat colors are exactly `#1C2026 #223039 #293E48 #31505E #3B6575 #4C7E8F #6A9EAC #9CC6CD`.
- Paper Light milestone colors are exactly `#20AE9B #796DE2 #F28D42 #E95078`.
- Paper Dark milestone colors are exactly `#4ED1BA #9A8CFF #FFB467 #FF7398`.
- Activity grids remain 52 columns by 7 rows with square cells, `2px` cell radius, and `3px` gaps.
- Milestone thresholds remain 100M, 300M, 500M, and 1B tokens.
- Full Profile and Overview scrollers receive `8px` logical inline-end safety space without document-level horizontal overflow.
- Month, Year, 3D, Daily, Weekly, Cumulative, and legends share the updated Paper palette.
- Non-Paper themes, APIs, date ranges, token totals, aggregation, tooltip data, hit targets, and reduced-motion behavior remain unchanged.
- Never stage or commit `.superpowers/` visual-companion artifacts.

---

## File Structure

- `src/tokdash/static/theme-config.js`: owns per-theme heat arrays consumed by Month, Year, 3D, Profile, and legends.
- `src/tokdash/static/themes.css`: owns Paper Light and Dark milestone color variables and the Paper inset keyline.
- `src/tokdash/static/index.html`: owns shared Profile/Overview geometry, milestone shadow stacks, and horizontal scroller spacing.
- `tests/test_profile_stats_frontend.py`: asserts exact theme tokens and the static frontend contracts without introducing a browser-test dependency.

No new runtime files or dependencies are required.

### Task 1: Replace Paper heat and milestone theme tokens

**Files:**
- Modify: `tests/test_profile_stats_frontend.py:556-737`
- Modify: `src/tokdash/static/theme-config.js:29-32`
- Modify: `src/tokdash/static/themes.css:133-140`
- Modify: `src/tokdash/static/themes.css:244-251`

**Interfaces:**
- Consumes: existing `themeConfig.heatColorsMap.paper.{light,dark}` arrays and `--profile-milestone-{1..4}` CSS variables.
- Produces: the exact Rain-cleared Sky tokens used by all existing renderers; no function signatures change.

- [ ] **Step 1: Replace the existing palette assertions with failing Rain-cleared Sky expectations**

Rename `test_paper_uses_approved_slate_ink_heat_palette` to `test_paper_uses_rain_cleared_sky_heat_palette` and use these expectations:

```python
def test_paper_uses_rain_cleared_sky_heat_palette():
    light, dark = _heat_palette_for("paper")
    assert light == [
        "#F6F2EA", "#E4EFF0", "#CCE4E6", "#A9D4DA",
        "#7FBCC8", "#559FB2", "#39798F", "#27566F",
    ]
    assert dark == [
        "#1C2026", "#223039", "#293E48", "#31505E",
        "#3B6575", "#4C7E8F", "#6A9EAC", "#9CC6CD",
    ]

    profile_indices = [round((level / 4) * (len(light) - 1)) for level in range(5)]
    assert profile_indices == [0, 2, 4, 5, 7]
    assert [light[index] for index in profile_indices] == [
        "#F6F2EA", "#CCE4E6", "#7FBCC8", "#559FB2", "#27566F",
    ]
    assert [dark[index] for index in profile_indices] == [
        "#1C2026", "#293E48", "#3B6575", "#4C7E8F", "#9CC6CD",
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

Rename `test_paper_uses_mineral_spectrum_milestones_and_keyline` to `test_paper_uses_rain_cleared_sky_milestones_and_keyline` and replace only its Paper rules with:

```python
    light_rule = """
html[data-ui-theme="paper"] .profile-activity-shell,
html[data-ui-theme="paper"] .overview-profile-band {
  --profile-milestone-1: #20AE9B;
  --profile-milestone-2: #796DE2;
  --profile-milestone-3: #F28D42;
  --profile-milestone-4: #E95078;
  --profile-milestone-keyline: var(--color-bg);
}
""".strip()
    dark_rule = """
html.dark[data-ui-theme="paper"] .profile-activity-shell,
html.dark[data-ui-theme="paper"] .overview-profile-band {
  --profile-milestone-1: #4ED1BA;
  --profile-milestone-2: #9A8CFF;
  --profile-milestone-3: #FFB467;
  --profile-milestone-4: #FF7398;
  --profile-milestone-keyline: var(--color-bg);
}
""".strip()
```

Keep the existing assertions for the transparent fallback, inset keyline count, and fallback milestone colors.

- [ ] **Step 2: Run the two focused tests and verify that the old tokens fail**

Run:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt \
  pytest -q \
  tests/test_profile_stats_frontend.py::test_paper_uses_rain_cleared_sky_heat_palette \
  tests/test_profile_stats_frontend.py::test_paper_uses_rain_cleared_sky_milestones_and_keyline
```

Expected: both tests fail because the source still contains Slate Ink heat colors and Mineral Spectrum milestone variables.

- [ ] **Step 3: Replace only the Paper runtime tokens**

In `theme-config.js`, set:

```javascript
      paper: {
        light: ["#F6F2EA", "#E4EFF0", "#CCE4E6", "#A9D4DA", "#7FBCC8", "#559FB2", "#39798F", "#27566F"],
        dark: ["#1C2026", "#223039", "#293E48", "#31505E", "#3B6575", "#4C7E8F", "#6A9EAC", "#9CC6CD"],
      },
```

In `themes.css`, set the Paper Light variables to:

```css
  --profile-milestone-1: #20AE9B;
  --profile-milestone-2: #796DE2;
  --profile-milestone-3: #F28D42;
  --profile-milestone-4: #E95078;
```

Set the Paper Dark variables to:

```css
  --profile-milestone-1: #4ED1BA;
  --profile-milestone-2: #9A8CFF;
  --profile-milestone-3: #FFB467;
  --profile-milestone-4: #FF7398;
```

Retain `--profile-milestone-keyline: var(--color-bg);` in both Paper rules.

- [ ] **Step 4: Run token tests and JavaScript syntax validation**

Run:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt \
  pytest -q \
  tests/test_profile_stats_frontend.py::test_paper_uses_rain_cleared_sky_heat_palette \
  tests/test_profile_stats_frontend.py::test_paper_uses_rain_cleared_sky_milestones_and_keyline
node --check src/tokdash/static/theme-config.js
```

Expected: `2 passed` and `node --check` exits with status 0 and no diagnostics.

- [ ] **Step 5: Commit the theme-token change**

```bash
git add src/tokdash/static/theme-config.js src/tokdash/static/themes.css tests/test_profile_stats_frontend.py
git commit -m "style: apply Rain-cleared Sky palette"
```

### Task 2: Strengthen milestone auras and add the right-edge gutter

**Files:**
- Modify: `tests/test_profile_stats_frontend.py:543-590`
- Modify: `src/tokdash/static/index.html:464-511`
- Modify: `src/tokdash/static/index.html:548-558`

**Interfaces:**
- Consumes: existing `data-milestone="1"` through `data-milestone="4"` attributes and `--profile-milestone-tone`/`--profile-milestone-keyline` variables.
- Produces: stronger CSS-only shadows plus `8px` logical inline-end scroller padding; DOM, hit targets, and renderer functions remain unchanged.

- [ ] **Step 1: Add a failing aura, geometry, and edge-gutter contract test**

Add this test after the Paper milestone-token test:

```python
def test_profile_uses_github_geometry_stronger_auras_and_edge_gutter():
    source = INDEX_HTML.read_text(encoding="utf-8")
    compact = re.sub(r"\s+", "", source)

    assert ".profile-activity-grid{" in compact
    assert "grid-template-columns:repeat(52,minmax(8px,1fr))" in compact
    assert "grid-template-rows:repeat(7,minmax(8px,1fr))" in compact
    assert "gap:3px" in compact
    assert ".profile-activity-cell{" in compact
    assert "border-radius:2px" in compact

    assert (
        ".profile-activity-scroll{overflow-x:auto;"
        "padding-block:8px12px;padding-inline:08px;}"
    ) in compact
    assert (
        ".overview-profile-scroll{overflow-x:auto;"
        "padding-block:2px4px;padding-inline:08px;}"
    ) in compact

    for fragment in [
        "0002pxcolor-mix(insrgb,var(--profile-milestone-tone)86%,transparent)",
        "0011pxcolor-mix(insrgb,var(--profile-milestone-tone)72%,transparent)",
        "0014pxcolor-mix(insrgb,var(--profile-milestone-tone)80%,transparent)",
        "0003pxcolor-mix(insrgb,var(--profile-milestone-tone)72%,transparent)",
        "0017pxcolor-mix(insrgb,var(--profile-milestone-tone)88%,transparent)",
        "0004pxcolor-mix(insrgb,var(--profile-milestone-tone)78%,transparent)",
        "0022pxcolor-mix(insrgb,var(--profile-milestone-tone)96%,transparent)",
    ]:
        assert fragment in compact

    for level in range(1, 5):
        assert f'.overview-profile-cell[data-milestone="{level}"]' in source
```

- [ ] **Step 2: Run the new test and verify that old aura values and padding fail**

Run:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt \
  pytest -q tests/test_profile_stats_frontend.py::test_profile_uses_github_geometry_stronger_auras_and_edge_gutter
```

Expected: FAIL because the scrollers have no logical inline-end padding and the current shadow stacks use weaker ring and blur values.

- [ ] **Step 3: Preserve geometry and add logical inline-end scroll space**

Replace the full Profile scroller rule with:

```css
.profile-activity-scroll{overflow-x:auto;padding-block:8px 12px;padding-inline:0 8px;}
```

Replace the Overview scroller rule with:

```css
.overview-profile-scroll{overflow-x:auto;padding-block:2px 4px;padding-inline:0 8px;}
```

Do not change `.profile-activity-grid`, `.overview-profile-grid`, `.profile-activity-cell`, or `.overview-profile-cell` geometry.

- [ ] **Step 4: Replace the full Profile milestone shadows with the approved progressive aura**

Use these exact rules:

```css
.profile-activity-cell[data-milestone="1"]{box-shadow:inset 0 0 0 1px var(--profile-milestone-keyline),0 0 0 2px color-mix(in srgb,var(--profile-milestone-tone) 86%,transparent),0 0 11px color-mix(in srgb,var(--profile-milestone-tone) 72%,transparent);}
.profile-activity-cell[data-milestone="2"]{box-shadow:inset 0 0 0 1px var(--profile-milestone-keyline),0 0 0 2px color-mix(in srgb,var(--profile-milestone-tone) 92%,transparent),0 0 14px color-mix(in srgb,var(--profile-milestone-tone) 80%,transparent);}
.profile-activity-cell[data-milestone="3"]{box-shadow:inset 0 0 0 1px var(--profile-milestone-keyline),0 0 0 1px color-mix(in srgb,var(--color-text) 82%,transparent),0 0 0 3px color-mix(in srgb,var(--profile-milestone-tone) 72%,transparent),0 0 17px color-mix(in srgb,var(--profile-milestone-tone) 88%,transparent);}
.profile-activity-cell[data-milestone="4"]{box-shadow:inset 0 0 0 1px var(--profile-milestone-keyline),0 0 0 2px color-mix(in srgb,var(--color-text) 92%,transparent),0 0 0 4px color-mix(in srgb,var(--profile-milestone-tone) 78%,transparent),0 0 22px color-mix(in srgb,var(--profile-milestone-tone) 96%,transparent);}
button.profile-activity-cell[data-milestone]:not(:disabled):is(:hover,:focus-visible),.profile-activity-cell[data-milestone].is-column-hover{box-shadow:inset 0 0 0 1px var(--profile-milestone-keyline),0 0 0 2px color-mix(in srgb,var(--color-text) 94%,transparent),0 0 0 4px color-mix(in srgb,var(--profile-milestone-tone) 84%,transparent),0 0 26px color-mix(in srgb,var(--profile-milestone-tone) 96%,transparent);}
```

The inset Paper keyline remains the first shadow in every stack.

- [ ] **Step 5: Add scaled Overview overrides for all four tiers**

Replace the three existing Overview overrides with:

```css
.overview-profile-cell[data-milestone="1"]{box-shadow:inset 0 0 0 1px var(--profile-milestone-keyline),0 0 0 1px color-mix(in srgb,var(--profile-milestone-tone) 72%,transparent),0 0 6px color-mix(in srgb,var(--profile-milestone-tone) 42%,transparent);}
.overview-profile-cell[data-milestone="2"]{box-shadow:inset 0 0 0 1px var(--profile-milestone-keyline),0 0 0 1px color-mix(in srgb,var(--profile-milestone-tone) 78%,transparent),0 0 8px color-mix(in srgb,var(--profile-milestone-tone) 52%,transparent);}
.overview-profile-cell[data-milestone="3"]{box-shadow:inset 0 0 0 1px var(--profile-milestone-keyline),0 0 0 1px color-mix(in srgb,var(--color-text) 74%,transparent),0 0 0 2px color-mix(in srgb,var(--profile-milestone-tone) 48%,transparent),0 0 10px color-mix(in srgb,var(--profile-milestone-tone) 62%,transparent);}
.overview-profile-cell[data-milestone="4"]{box-shadow:inset 0 0 0 1px var(--profile-milestone-keyline),0 0 0 1px color-mix(in srgb,var(--color-text) 82%,transparent),0 0 0 3px color-mix(in srgb,var(--profile-milestone-tone) 58%,transparent),0 0 13px color-mix(in srgb,var(--profile-milestone-tone) 72%,transparent);}
```

- [ ] **Step 6: Run focused frontend regression tests**

Run:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt \
  pytest -q tests/test_profile_stats_frontend.py
```

Expected: all tests in `tests/test_profile_stats_frontend.py` pass.

- [ ] **Step 7: Commit the aura and gutter change**

```bash
git add src/tokdash/static/index.html tests/test_profile_stats_frontend.py
git commit -m "style: strengthen Profile milestone aura"
```

### Task 3: Run full regression and visual verification

**Files:**
- Verify: `src/tokdash/static/theme-config.js`
- Verify: `src/tokdash/static/themes.css`
- Verify: `src/tokdash/static/index.html`
- Verify: `tests/test_profile_stats_frontend.py`

**Interfaces:**
- Consumes: the completed theme-token and CSS contracts from Tasks 1 and 2.
- Produces: evidence that the update is compatible with the existing application; no new runtime interface.

- [ ] **Step 1: Run the complete automated suite**

Run:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt pytest -q
```

Expected: the known baseline may remain `1 failed, 708 passed, 3 skipped` after adding the new contract test, with the sole failure at `tests/test_period_semantics.py::test_previous_period_range_month_uses_full_previous_calendar_month`; no new failure may be introduced. If the baseline test has since been fixed, expect the entire suite to pass.

- [ ] **Step 2: Run the repository's compile check**

Run:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt \
  python -m compileall -q src/tokdash main.py docs/guides/agents/openclaw_reporting/openclaw_cron_job.py
```

Expected: exit status 0 with no diagnostics.

- [ ] **Step 3: Discover and run configured type-check and lint commands**

Run:

```bash
rg -n "\[tool\.(ruff|mypy|pyright)|ruff|mypy|pyright|eslint|typecheck|lint" \
  pyproject.toml requirements-dev.txt .github 2>/dev/null || true
```

Expected in the current repository: no output, because no type-checker or linter is configured. If configuration appears before execution, run the discovered project command and record its exact diagnostics.

- [ ] **Step 4: Ensure the local server is available**

Check:

```bash
curl -fsS http://127.0.0.1:55424/health
```

Expected: HTTP 200. If the server is not running, start it with:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt \
  tokdash serve --bind 127.0.0.1 --port 55424 --no-open
```

- [ ] **Step 5: Verify Paper Light and Dark in the browser**

At `http://127.0.0.1:55424/`, verify:

1. Overview and full Profile both render Rain-cleared Sky heat colors.
2. Daily cells remain square with `2px` radius and `3px` gaps.
3. Weekly and Cumulative keep the same day-column geometry and synchronized mode controls.
4. 100M, 300M, 500M, and 1B use teal, violet, orange, and peach-red with visibly progressive aura strength.
5. Dark mode uses the brighter night-derived milestone colors and the eight dark heat levels.
6. Tooltips remain readable and retain milestone badges, token breakdown, and cost.

- [ ] **Step 6: Verify the rightmost cell and responsive behavior**

At the default viewport and an explicit `795x900` viewport:

1. Scroll both Profile and Overview activity scrollers fully to the inline end.
2. Confirm the final 1B cell and its outer aura are fully visible.
3. Confirm the internal scroller exposes the intended `8px` end space.
4. Confirm `document.documentElement.scrollWidth <= window.innerWidth`.
5. Reset the temporary viewport override after verification.

- [ ] **Step 7: Verify other Paper and non-Paper surfaces**

1. In Paper, inspect Month, Year, and 3D; each legend and rendered cell must use the new eight-level Light/Dark arrays.
2. Switch to Classic and confirm its heat colors remain `#EEF2F7 ... #1E40AF` in Light and `#172033 ... #BFDBFE` in Dark.
3. Confirm Classic milestone fallback remains cyan, violet, amber, and pink with a transparent keyline.
4. Inspect browser error logs and require zero new console errors.

- [ ] **Step 8: Audit the final change boundary**

Run:

```bash
git diff --check f3d200f..HEAD
git status --short
git log -6 --oneline --decorate
```

Expected: only the two implementation commits plus the approved design/plan documentation are in scope; `.superpowers/` remains untracked and unstaged. Do not push or open a pull request until the user explicitly approves the local result.
