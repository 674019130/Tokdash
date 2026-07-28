# Profile Activity Grid Spacing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Increase Profile and Overview activity-grid spacing from `3px` to `3.5px` while preserving square cells, aura visibility, overlay alignment, and contained responsive scrolling.

**Architecture:** Keep the existing HTML and rendering code intact. Treat the day grid, Weekly hit overlay, month labels, legend, and compact Overview grid as one synchronized CSS geometry unit, then lock that geometry with focused source-contract tests and browser measurements.

**Tech Stack:** Static HTML/CSS in `src/tokdash/static/index.html`, Python `pytest` source-contract tests, `uv`, and the in-app browser for visual and responsive verification.

## Global Constraints

- Use `3.5px` for `.profile-activity-grid`, `.profile-activity-week-hits`, `.overview-profile-grid`, and `.overview-profile-week-hits`.
- Use `595px` for `.profile-activity-grid-wrap`, `.profile-activity-months`, `.profile-activity-legend`, and `.overview-profile-grid-wrap`.
- Preserve 52 columns by 7 rows, square cells, `2px` cell radius, and an `8px` minimum cell track.
- Preserve the Profile aura reserve at `26px + 8px` and the Overview aura reserve at `16px + 8px`.
- Do not change heat colors, milestone thresholds, aura radii, aggregation, tooltip behavior, DOM structure, API responses, or persisted data.
- Keep document-level horizontal overflow at zero; any required narrow-screen scrolling stays inside the activity scroller.
- Preserve the existing untracked `.superpowers/` visual-companion artifacts and unrelated user changes.
- Never delete generated files; archive an unwanted generated artifact with a reason if a command creates one.

---

### Task 1: Synchronize Profile and Overview Activity Geometry

**Files:**
- Modify: `tests/test_profile_stats_frontend.py:595-664`
- Modify: `tests/test_profile_stats_frontend.py:838-891`
- Modify: `src/tokdash/static/index.html:464-475`
- Modify: `src/tokdash/static/index.html:514-515`
- Modify: `src/tokdash/static/index.html:550-554`

**Interfaces:**
- Consumes: Existing 52-by-7 CSS grids, Weekly overlay grids, Profile aura gutter variables, and Overview aura gutter variables.
- Produces: A synchronized `3.5px` activity-grid gap and `595px` aligned minimum width for both full and compact presentations.

- [ ] **Step 1: Update the focused geometry contract tests so they describe the approved spacing**

In `test_profile_uses_github_geometry_stronger_auras_and_edge_gutter`, replace the broad Profile gap assertion with these exact geometry checks:

```python
    assert (
        ".profile-activity-grid-wrap{position:relative;min-width:595px;}"
        in compact
    )
    assert (
        ".profile-activity-grid{display:grid;grid-auto-flow:column;"
        "grid-template-columns:repeat(52,minmax(8px,1fr));"
        "grid-template-rows:repeat(7,minmax(8px,1fr));"
        "gap:3.5px;width:100%;}"
        in compact
    )
    assert (
        ".profile-activity-week-hits{position:absolute;inset:0;display:grid;"
        "grid-template-columns:repeat(52,minmax(8px,1fr));"
        "gap:3.5px;pointer-events:none;}"
        in compact
    )
    assert (
        ".profile-activity-months{display:flex;justify-content:space-between;"
        "min-width:595px;"
        in compact
    )
    assert (
        ".profile-activity-legend{display:flex;align-items:center;"
        "justify-content:flex-end;gap:8px;min-width:595px;"
        in compact
    )
```

Keep these existing cell-shape checks immediately after the new block:

```python
    assert ".profile-activity-cell{" in compact
    assert "border-radius:2px" in compact
```

In `test_overview_profile_summary_markup_and_style_contract`, replace the broad Overview gap and grid-wrap checks with:

```python
    assert (
        ".overview-profile-grid-wrap{position:relative;min-width:595px;}"
        in compact
    )
    assert (
        ".overview-profile-grid{display:grid;grid-auto-flow:column;"
        "grid-template-columns:repeat(52,minmax(8px,1fr));"
        "grid-template-rows:repeat(7,minmax(8px,1fr));"
        "gap:3.5px;width:100%;}"
        in compact
    )
    assert (
        ".overview-profile-week-hits{"
        "grid-template-columns:repeat(52,minmax(8px,1fr));"
        "gap:3.5px;}"
        in compact
    )
    assert ".overview-profile-cell{border-radius:2px" in compact
```

- [ ] **Step 2: Run the two focused tests and verify that the old geometry fails**

Run:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest \
  pytest -q \
  tests/test_profile_stats_frontend.py::test_profile_uses_github_geometry_stronger_auras_and_edge_gutter \
  tests/test_profile_stats_frontend.py::test_overview_profile_summary_markup_and_style_contract
```

Expected: both tests fail because `index.html` still uses `3px` gaps and `572px` minimum widths.

- [ ] **Step 3: Apply the minimal synchronized CSS geometry change**

Replace the affected Profile rules with:

```css
.profile-activity-grid-wrap{position:relative;min-width:595px;}
.profile-activity-grid{display:grid;grid-auto-flow:column;grid-template-columns:repeat(52,minmax(8px,1fr));grid-template-rows:repeat(7,minmax(8px,1fr));gap:3.5px;width:100%;}
.profile-activity-week-hits{position:absolute;inset:0;display:grid;grid-template-columns:repeat(52,minmax(8px,1fr));gap:3.5px;pointer-events:none;}
.profile-activity-months{display:flex;justify-content:space-between;min-width:595px;margin-top:8px;color:var(--color-muted);font-size:12px;}
.profile-activity-legend{display:flex;align-items:center;justify-content:flex-end;gap:8px;min-width:595px;margin-top:10px;color:var(--color-muted);font-size:10px;line-height:1;white-space:nowrap;}
```

Replace the affected Overview rules with:

```css
.overview-profile-grid-wrap{position:relative;min-width:595px;}
.overview-profile-grid{display:grid;grid-auto-flow:column;grid-template-columns:repeat(52,minmax(8px,1fr));grid-template-rows:repeat(7,minmax(8px,1fr));gap:3.5px;width:100%;}
.overview-profile-week-hits{grid-template-columns:repeat(52,minmax(8px,1fr));gap:3.5px;}
```

Do not edit the cell radius, aura shadows, aura-reserve variables, edge-safety gutter, or any rendering JavaScript.

- [ ] **Step 4: Re-run the focused tests and verify they pass**

Run:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest \
  pytest -q \
  tests/test_profile_stats_frontend.py::test_profile_uses_github_geometry_stronger_auras_and_edge_gutter \
  tests/test_profile_stats_frontend.py::test_overview_profile_summary_markup_and_style_contract
```

Expected: `2 passed`.

- [ ] **Step 5: Run the complete frontend contract file**

Run:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest \
  pytest -q tests/test_profile_stats_frontend.py
```

Expected: all frontend contract tests pass.

- [ ] **Step 6: Check the task diff and commit the implementation**

Run:

```bash
git diff --check
git diff -- src/tokdash/static/index.html tests/test_profile_stats_frontend.py
git status --short
```

Expected: no whitespace errors; only the two planned files are modified, plus the pre-existing untracked `.superpowers/` directory.

Commit:

```bash
git add src/tokdash/static/index.html tests/test_profile_stats_frontend.py
git commit -m "style: give activity auras more room"
```

---

### Task 2: Full Automated and Browser Regression Verification

**Files:**
- Verify: `src/tokdash/static/index.html`
- Verify: `tests/test_profile_stats_frontend.py`
- Verify: `.github/workflows/ci.yml`
- Verify: `pyproject.toml`
- Verify: `requirements-dev.txt`

**Interfaces:**
- Consumes: The committed `3.5px`/`595px` activity geometry from Task 1.
- Produces: Evidence that the geometry remains aligned, responsive, compatible, and free of new automated-test failures.

- [ ] **Step 1: Run the full test suite**

Run:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest pytest -q
```

Expected baseline: `1 failed, 708 passed, 3 skipped`, with the only failure being the existing case:

```text
tests/test_period_semantics.py::test_previous_period_range_month_uses_full_previous_calendar_month
Expected: 2026-02-01 00:00 UTC
Actual:   2026-01-31 16:00 UTC
```

No new failure may be attributed to the spacing change.

- [ ] **Step 2: Run the CI-equivalent Python compilation check**

Run:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt \
  python -m compileall -q \
  src/tokdash main.py docs/guides/agents/openclaw_reporting/openclaw_cron_job.py tests
```

Expected: exit code `0` with no diagnostics.

- [ ] **Step 3: Discover and run configured type-check and lint commands**

Run:

```bash
rg -n "\[tool\.(ruff|mypy|pyright)|ruff|mypy|pyright|eslint|typecheck|lint" \
  pyproject.toml requirements-dev.txt .github 2>/dev/null || true
```

Expected for the current repository: no configured type-check or lint target. If the command finds a configured target, run that exact target and record its diagnostics.

- [ ] **Step 4: Verify the running local service**

Run:

```bash
curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:55424/
curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:55424/health
```

Expected: `200` for both endpoints. If the existing process is no longer running, start Tokdash from the repository root and keep it running for user review:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt \
  tokdash serve --bind 127.0.0.1 --port 55424 --no-open
```

- [ ] **Step 5: Verify Profile geometry in the browser at default and narrow widths**

Use the in-app browser skill and the existing local Tokdash tab. Select Paper Light, Profile, and Daily through visible controls. When internal scrolling is present, use the activity scroller to move to its right edge before measuring clearance. At the default viewport and at `795x900`, evaluate:

```javascript
(() => {
  const scroller = document.getElementById("profileActivityScroller");
  const grid = document.getElementById("profileActivityGrid");
  const cell = grid.firstElementChild;
  const scrollerRect = scroller.getBoundingClientRect();
  const gridRect = grid.getBoundingClientRect();
  const cellRect = cell.getBoundingClientRect();
  const style = getComputedStyle(grid);
  return {
    gap: style.gap,
    columns: style.gridTemplateColumns.split(" ").length,
    cellWidth: cellRect.width,
    cellHeight: cellRect.height,
    radius: getComputedStyle(cell).borderRadius,
    rightClearance: scrollerRect.right - gridRect.right,
    documentOverflow: Math.max(0, document.documentElement.scrollWidth - innerWidth),
    scrollContained: scroller.scrollWidth >= scroller.clientWidth,
  };
})()
```

Expected at both sizes:

- `gap` is `3.5px`.
- `columns` is `52`.
- `cellWidth` equals `cellHeight` within normal subpixel rounding.
- `radius` is `2px`.
- `rightClearance` is `34px` when scrolled to the right edge.
- `documentOverflow` is `0`.
- The rightmost milestone ring and aura are fully visible.

Switch Daily, Weekly, and Cumulative through the visible mode controls. Confirm the mode state changes, Weekly overlays remain column-aligned, and the rightmost milestone remains visible.

- [ ] **Step 6: Verify Overview geometry, themes, and contained scrolling**

Open Overview through its visible control. At the default viewport and at `795x900`, move the Overview activity scroller to its right edge when internal scrolling is present, then evaluate the same geometry using:

```javascript
(() => {
  const scroller = document.getElementById("overviewProfileScroller");
  const grid = document.getElementById("overviewProfileGrid");
  const cell = grid.firstElementChild;
  const scrollerRect = scroller.getBoundingClientRect();
  const gridRect = grid.getBoundingClientRect();
  const cellRect = cell.getBoundingClientRect();
  const style = getComputedStyle(grid);
  return {
    gap: style.gap,
    columns: style.gridTemplateColumns.split(" ").length,
    cellWidth: cellRect.width,
    cellHeight: cellRect.height,
    radius: getComputedStyle(cell).borderRadius,
    rightClearance: scrollerRect.right - gridRect.right,
    documentOverflow: Math.max(0, document.documentElement.scrollWidth - innerWidth),
    clientWidth: scroller.clientWidth,
    scrollWidth: scroller.scrollWidth,
  };
})()
```

Expected:

- `gap` is `3.5px`; `columns` is `52`; cells remain square with `2px` radius.
- `rightClearance` is `24px` when scrolled to the right edge.
- `documentOverflow` is `0`.
- If `scrollWidth > clientWidth`, the scrollbar belongs only to `overviewProfileScroller` and the rightmost milestone becomes fully visible at the scroll end.
- Daily, Weekly, and Cumulative controls stay synchronized with the full Profile view.

Repeat Profile and Overview checks in Paper Dark. Confirm Rain-cleared Sky colors and milestone auras are unchanged except for the increased space between cells. Briefly select Classic and confirm its heat colors remain unchanged.

- [ ] **Step 7: Restore the review state and inspect browser diagnostics**

Reset the temporary viewport override. Leave the handoff tab on Paper Light, Profile, Daily at the default viewport. Inspect browser logs.

Expected: no console `error` entries. The existing Tailwind CDN and deprecated Three.js build warnings may remain.

- [ ] **Step 8: Perform the final repository audit**

Run:

```bash
git diff --check 5377ec0..HEAD
git status --short
git log -6 --oneline --decorate
git diff --stat 5377ec0..HEAD
```

Expected:

- `git diff --check` exits `0`.
- The implementation commit contains only `src/tokdash/static/index.html` and `tests/test_profile_stats_frontend.py`.
- The working tree contains no new modification; the pre-existing `.superpowers/` directory remains untracked and untouched.
- Do not push or open a pull request until the user explicitly approves the local result.
