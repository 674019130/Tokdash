# Profile Activity Legend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a compact, mode-aware activity and milestone legend to both the complete Profile heatmap and the Overview Profile band.

**Architecture:** Keep the feature frontend-only in the existing embedded `index.html`. Add one safe DOM legend renderer driven by the existing `profileActivityMode`, mount it in the current activity scrollers, and reuse the existing heat colors, milestone tokens, localization state, and Overview/Profile rerender paths.

**Tech Stack:** HTML/CSS, vanilla browser JavaScript embedded in `src/tokdash/static/index.html`, Python 3.10+ pytest contract tests, Node.js whole-script syntax validation, existing FastAPI/Uvicorn local server.

## Global Constraints

- Implement only `docs/superpowers/specs/2026-07-27-profile-activity-legend-design.md`.
- Stay on the current normal branch `feat/profile-stats-view`; do not create a linked worktree.
- Modify only `src/tokdash/static/index.html` and `tests/test_profile_stats_frontend.py` during functional implementation.
- Never delete files. Do not stage or commit `.superpowers/` visual-companion artifacts.
- Complete Profile places the legend below its existing month labels. Overview places it directly below the grid and does not add month labels.
- Daily uses five square heat swatches. Weekly and Cumulative use a five-step ascending-column glyph.
- Always show `100M`, `300M`, `500M`, and `1B` badges using the existing tier-1 through tier-4 colors.
- Keep the legend inside the existing activity scroller and aligned to the 52-week grid's `572px` minimum width.
- Keep Overview's legend quieter and tighter than Profile's legend.
- Use `createElement`, `textContent`, and `replaceChildren`; do not interpolate data through `innerHTML`.
- Reuse `profileActivityMode`, `getProfileActivityColor(level)`, `t(key)`, and `--profile-milestone-*`. Do not add an API request, persistence, cache mutation, backend contract, or new milestone semantics.
- Preserve the existing 52×7 geometry, 3 px gap, 2 px cell radius, tooltips, keyboard interaction, reduced motion, loading/error states, theme behavior, and reload default.
- Reuse existing `less`, `more`, and `milestone` translations; add only the missing localized activity-legend label.
- Before handoff, run the focused frontend file, the CI compile command, the full pytest suite, the existing whole-script Node syntax test, and configured type-check/lint discovery. Report exact diagnostics for any existing failure.
- Call out the intentional behavior change: ready Overview and Profile activity surfaces gain an always-visible, mode-aware legend. Calculations and backend behavior remain unchanged.

## File Map

- Modify: `src/tokdash/static/index.html`
  - Owns legend hosts, shared CSS, localized label, safe DOM renderer, and calls from existing Profile/Overview render paths.
- Modify: `tests/test_profile_stats_frontend.py`
  - Owns markup, localization, safe-rendering, mode-awareness, shared-state, and responsive style contracts.
- Reference only: `docs/superpowers/specs/2026-07-27-profile-activity-legend-design.md`
  - Approved layout, semantics, accessibility, compatibility, and out-of-scope boundaries.

---

### Task 1: Add the Shared Legend Renderer to the Complete Profile

**Files:**
- Modify: `tests/test_profile_stats_frontend.py:543-612`
- Modify: `src/tokdash/static/index.html:447-513, 2352-2353, 2605-2606, 1641-1664, 6226-6511`

**Interfaces:**
- Consumes: `profileActivityMode: 'daily'|'weekly'|'cumulative'`, `getProfileActivityColor(level) -> string`, `t(key) -> string`, and existing `--profile-milestone-1..4` tokens.
- Produces: `renderProfileActivityLegend(targetId: string, mode: string) -> void`, `#profileActivityLegend`, localized `activityLegend`, and shared `.profile-activity-legend*` CSS primitives for Task 2.

- [ ] **Step 1: Write the failing Profile legend contract test**

Add after `test_profile_visual_polish_contract`:

```python
def test_profile_activity_legend_is_safe_localized_and_mode_aware():
    source = INDEX_HTML.read_text(encoding="utf-8")
    compact = re.sub(r"\s+", "", source)

    assert 'id="profileActivityLegend"' in source
    assert source.count("activityLegend: '") == 2
    assert ".profile-activity-legend{" in compact
    assert ".profile-activity-legend-swatches{" in compact
    assert ".profile-activity-legend-bars{" in compact
    assert ".profile-activity-legend-badge{" in compact

    renderer = _extract_js_function(
        source,
        "function renderProfileActivityLegend(targetId, mode) {",
    )
    assert "document.createElement(" in renderer
    assert "legend.replaceChildren(scale, divider, milestones);" in renderer
    assert "mode === 'daily'" in renderer
    assert "getProfileActivityColor(level)" in renderer
    assert "profile-activity-legend-bars" in renderer
    assert "profile-activity-legend-badge" in renderer
    assert "glyph.setAttribute('aria-hidden', 'true');" in renderer
    assert ".innerHTML" not in renderer

    profile_renderer = _extract_js_function(
        source,
        "function renderProfileView() {",
    )
    assert (
        "renderProfileActivityLegend('profileActivityLegend', profileActivityMode);"
        in profile_renderer
    )
```

Also append `"profileActivityLegend"` to `required_ids` in `test_profile_view_html_and_localization_contract`.

- [ ] **Step 2: Run the new tests and verify the intended failure**

Run:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest \
  tests/test_profile_stats_frontend.py::test_profile_activity_legend_is_safe_localized_and_mode_aware \
  tests/test_profile_stats_frontend.py::test_profile_view_html_and_localization_contract -q
```

Expected: FAIL because `profileActivityLegend`, `activityLegend`, the renderer, and legend CSS do not exist.

- [ ] **Step 3: Add the shared legend CSS**

Add immediately after `.profile-activity-months`:

```css
.profile-activity-legend{display:flex;align-items:center;justify-content:flex-end;gap:8px;min-width:572px;margin-top:10px;color:var(--color-muted);font-size:10px;line-height:1;white-space:nowrap;}
.profile-activity-legend-scale,.profile-activity-legend-milestones{display:flex;align-items:center;gap:5px;}
.profile-activity-legend-glyph{display:flex;align-items:center;gap:3px;height:12px;}
.profile-activity-legend-swatch{width:10px;height:10px;border-radius:2px;box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--color-text) 7%,transparent);}
.profile-activity-legend-bars{align-items:flex-end;}
.profile-activity-legend-bar{width:6px;border-radius:2px 2px 1px 1px;background:var(--color-primary);opacity:.82;}
.profile-activity-legend-bar:nth-child(1){height:3px;}.profile-activity-legend-bar:nth-child(2){height:5px;}.profile-activity-legend-bar:nth-child(3){height:7px;}.profile-activity-legend-bar:nth-child(4){height:9px;}.profile-activity-legend-bar:nth-child(5){height:12px;}
.profile-activity-legend-divider{width:1px;height:12px;background:var(--color-border);}
.profile-activity-legend-badge{padding:3px 5px;border:1px solid color-mix(in srgb,var(--profile-milestone-tone) 54%,transparent);border-radius:999px;background:color-mix(in srgb,var(--profile-milestone-tone) 7%,transparent);color:var(--profile-milestone-tone);font-size:8px;font-weight:850;letter-spacing:.02em;}
.profile-activity-legend-badge[data-milestone="1"]{--profile-milestone-tone:var(--profile-milestone-1);}.profile-activity-legend-badge[data-milestone="2"]{--profile-milestone-tone:var(--profile-milestone-2);}.profile-activity-legend-badge[data-milestone="3"]{--profile-milestone-tone:var(--profile-milestone-3);}.profile-activity-legend-badge[data-milestone="4"]{--profile-milestone-tone:var(--profile-milestone-4);}
```

- [ ] **Step 4: Add the Profile legend host and localized label**

Add after `#profileActivityMonths`, inside `#profileActivityScroller`:

```html
<div id="profileActivityLegend" class="profile-activity-legend"></div>
```

Add to the English translation object near `less` and `more`:

```javascript
activityLegend: 'Token activity legend',
```

Add to the Simplified Chinese object in the equivalent location:

```javascript
activityLegend: 'Token 活跃度图例',
```

- [ ] **Step 5: Implement the safe shared renderer**

Add after `getProfileActivityColor`:

```javascript
function renderProfileActivityLegend(targetId, mode) {
  const legend = document.getElementById(targetId);
  if (!legend) return;
  const safeMode = ['daily', 'weekly', 'cumulative'].includes(mode) ? mode : 'daily';
  legend.dataset.mode = safeMode;
  legend.setAttribute('aria-label', t('activityLegend'));

  const scale = document.createElement('div');
  scale.className = 'profile-activity-legend-scale';
  const less = document.createElement('span');
  less.dataset.i18n = 'less';
  less.textContent = t('less');
  const glyph = document.createElement('span');
  glyph.className = safeMode === 'daily'
    ? 'profile-activity-legend-glyph profile-activity-legend-swatches'
    : 'profile-activity-legend-glyph profile-activity-legend-bars';
  glyph.setAttribute('aria-hidden', 'true');
  for (let level = 0; level < 5; level += 1) {
    const item = document.createElement('span');
    if (safeMode === 'daily') {
      item.className = 'profile-activity-legend-swatch';
      item.style.background = getProfileActivityColor(level);
    } else {
      item.className = 'profile-activity-legend-bar';
    }
    glyph.appendChild(item);
  }
  const more = document.createElement('span');
  more.dataset.i18n = 'more';
  more.textContent = t('more');
  scale.append(less, glyph, more);

  const divider = document.createElement('span');
  divider.className = 'profile-activity-legend-divider';
  divider.setAttribute('aria-hidden', 'true');
  const milestones = document.createElement('div');
  milestones.className = 'profile-activity-legend-milestones';
  [
    { level: 1, label: '100M' },
    { level: 2, label: '300M' },
    { level: 3, label: '500M' },
    { level: 4, label: '1B' },
  ].forEach(({ level, label }) => {
    const badge = document.createElement('span');
    badge.className = 'profile-activity-legend-badge';
    badge.dataset.milestone = String(level);
    badge.textContent = label;
    milestones.appendChild(badge);
  });

  legend.replaceChildren(scale, divider, milestones);
}
```

- [ ] **Step 6: Render the Profile legend with the current mode**

In `renderProfileView`, immediately after `renderProfileMonths(today);`, add:

```javascript
renderProfileActivityLegend('profileActivityLegend', profileActivityMode);
```

The existing `setProfileActivityMode` call to `renderProfileView()` updates the glyph without another fetch.

- [ ] **Step 7: Run the focused Profile tests**

Run:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest \
  tests/test_profile_stats_frontend.py::test_profile_activity_legend_is_safe_localized_and_mode_aware \
  tests/test_profile_stats_frontend.py::test_profile_view_html_and_localization_contract \
  tests/test_profile_stats_frontend.py::test_profile_visual_polish_contract \
  tests/test_profile_stats_frontend.py::test_main_inline_script_parses_with_node -q
```

Expected: all four tests PASS.

- [ ] **Step 8: Commit the complete Profile legend**

```bash
git add src/tokdash/static/index.html tests/test_profile_stats_frontend.py
git commit -m "feat: add profile activity legend"
```

---

### Task 2: Reuse the Legend in Overview and Keep Localization Synchronized

**Files:**
- Modify: `tests/test_profile_stats_frontend.py:616-770`
- Modify: `src/tokdash/static/index.html:527-590, 1124-1132, 3151-3194, 6526-6593`

**Interfaces:**
- Consumes: `renderProfileActivityLegend(targetId, mode)` and shared `.profile-activity-legend*` primitives from Task 1.
- Produces: `#overviewProfileLegend`, compact `.overview-profile-legend`, Overview render integration, and language-switch synchronization for both legend hosts.

- [ ] **Step 1: Write the failing Overview integration test**

Add after `test_overview_profile_modes_share_state_and_render_aggregate_hits_contract`:

```python
def test_overview_profile_legend_reuses_mode_and_scroller_contract():
    source = INDEX_HTML.read_text(encoding="utf-8")
    compact = re.sub(r"\s+", "", source)

    assert 'id="overviewProfileLegend"' in source
    assert source.index('id="overviewProfileGridWrap"') < source.index(
        'id="overviewProfileLegend"'
    ) < source.index('id="overviewProfileTooltip"')
    assert ".overview-profile-legend{" in compact

    renderer = _extract_js_function(
        source,
        "function renderOverviewProfilePreview(contributions = statsCache.default) {",
    )
    assert (
        "renderProfileActivityLegend('overviewProfileLegend', profileActivityMode);"
        in renderer
    )
    assert "fetch(" not in renderer

    i18n = _extract_js_function(source, "function applyI18n() {")
    assert "renderProfileActivityLegend('profileActivityLegend', profileActivityMode);" in i18n
    assert "renderProfileActivityLegend('overviewProfileLegend', profileActivityMode);" in i18n
```

Also append `"overviewProfileLegend"` to `required_ids` in `test_overview_profile_summary_markup_and_style_contract`.

- [ ] **Step 2: Run the new Overview tests and verify the intended failure**

Run:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest \
  tests/test_profile_stats_frontend.py::test_overview_profile_legend_reuses_mode_and_scroller_contract \
  tests/test_profile_stats_frontend.py::test_overview_profile_summary_markup_and_style_contract -q
```

Expected: FAIL because `overviewProfileLegend`, compact Overview styling, and renderer calls do not exist.

- [ ] **Step 3: Add the Overview legend host inside the existing scroller**

Add after `#overviewProfileGridWrap` and before the closing `#overviewProfileScroller` tag:

```html
<div id="overviewProfileLegend" class="profile-activity-legend overview-profile-legend"></div>
```

Do not add an Overview month-label row.

- [ ] **Step 4: Add the quieter Overview sizing**

Add near the other `.overview-profile-*` activity styles:

```css
.overview-profile-legend{margin-top:7px;gap:6px;font-size:9px;}
.overview-profile-legend .profile-activity-legend-scale,.overview-profile-legend .profile-activity-legend-milestones{gap:4px;}
.overview-profile-legend .profile-activity-legend-swatch{width:8px;height:8px;}
.overview-profile-legend .profile-activity-legend-glyph{height:10px;}
.overview-profile-legend .profile-activity-legend-bar:nth-child(5){height:10px;}
.overview-profile-legend .profile-activity-legend-badge{padding:2px 4px;font-size:7px;}
```

- [ ] **Step 5: Render Overview legend state without fetching**

In `renderOverviewProfilePreview`, after the grid and aggregate hit targets have been rebuilt and before `setOverviewProfileState('ready');`, add:

```javascript
renderProfileActivityLegend('overviewProfileLegend', profileActivityMode);
```

- [ ] **Step 6: Refresh both accessible labels on language changes**

At the end of `applyI18n`, after `syncDatePickerFooter();`, add:

```javascript
if (typeof profileActivityMode !== 'undefined') {
  renderProfileActivityLegend('profileActivityLegend', profileActivityMode);
  renderProfileActivityLegend('overviewProfileLegend', profileActivityMode);
}
```

The renderer safely returns for a missing host and uses localized `less`, `more`, and `activityLegend` text.

- [ ] **Step 7: Run Overview, synchronization, localization, and syntax tests**

Run:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest \
  tests/test_profile_stats_frontend.py::test_overview_profile_legend_reuses_mode_and_scroller_contract \
  tests/test_profile_stats_frontend.py::test_overview_profile_summary_markup_and_style_contract \
  tests/test_profile_stats_frontend.py::test_overview_profile_modes_share_state_and_render_aggregate_hits_contract \
  tests/test_profile_stats_frontend.py::test_profile_activity_legend_is_safe_localized_and_mode_aware \
  tests/test_profile_stats_frontend.py::test_main_inline_script_parses_with_node -q
```

Expected: all five tests PASS. The existing Overview renderer contract must still contain no `fetch(` call.

- [ ] **Step 8: Commit the Overview legend integration**

```bash
git add src/tokdash/static/index.html tests/test_profile_stats_frontend.py
git commit -m "feat: show activity legend on overview"
```

---

### Task 3: Regression, Type-Check Discovery, and Local Visual Verification

**Files:**
- Modify only if a verified defect is found: `src/tokdash/static/index.html`, `tests/test_profile_stats_frontend.py`

**Interfaces:**
- Consumes: Tasks 1 and 2.
- Produces: exact automated results, browser evidence, compatibility assessment, and a local build ready for user approval before any push or PR.

- [ ] **Step 1: Run the complete focused frontend file**

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest tests/test_profile_stats_frontend.py -q
```

Expected: all Profile frontend tests PASS, including `test_main_inline_script_parses_with_node`.

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

Expected: PASS. If the unrelated calendar-month timezone baseline failure remains, record its exact test name and traceback and confirm the focused file still passes.

- [ ] **Step 4: Perform the required type-check and lint discovery**

```bash
rg -n "\[tool\.(ruff|mypy|pyright)|ruff|mypy|pyright|eslint|typecheck|lint" \
  pyproject.toml requirements-dev.txt .github 2>/dev/null || true
```

Expected for the current repository: no configured Python/JavaScript static type-check or lint target. Report this exact command and result; do not call `compileall` or `node --check` a type checker.

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

- [ ] **Step 6: Verify both legends in the local browser**

At `http://127.0.0.1:55424/`, verify:

1. Overview ready state shows one right-aligned compact legend directly under the grid and no new month row.
2. Complete Profile shows the same legend below the existing month labels.
3. Daily shows five square swatches from the empty tone to the strongest heat tone.
4. Weekly and Cumulative show five ascending bars and do not show heat swatches.
5. Both surfaces always show `100M`, `300M`, `500M`, and `1B` badges with cyan, violet, amber, and pink tier colors.
6. Overview/Profile mode controls remain synchronized and changing modes issues no new `/api/stats` request.
7. English/Chinese switches update `Less`/`More` and the accessible legend label.
8. Light/dark themes preserve contrast.
9. At approximately 795 px and a wide viewport, `document.body.scrollWidth === document.documentElement.clientWidth`.
10. The rightmost 1B tooltip remains inside the viewport and does not overlap the legend enough to block reading.

- [ ] **Step 7: Inspect the final implementation scope**

Run:

```bash
git diff --check 1258413..HEAD
git status --short
git log -6 --oneline --decorate
```

Expected: no whitespace errors; only the approved source, test, design clarification, and plan/implementation commits are tracked. `.superpowers/` remains untracked and unstaged.

- [ ] **Step 8: Hand off locally before PR creation**

Report:

- the local URL;
- focused, compile, full-suite, syntax, type-check/lint discovery, and browser results;
- any unchanged baseline failure with exact diagnostics;
- intentional functional changes and compatibility risks;
- that no backend/API/calculation behavior changed;
- that nothing was pushed and no PR was created pending user approval.
