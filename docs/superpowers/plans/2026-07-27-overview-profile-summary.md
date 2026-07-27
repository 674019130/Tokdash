# Overview Profile Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a compact 52-week Daily Profile activity band after the Overview charts without changing their size, adding a network request, or duplicating the full Stats → Profile experience.

**Architecture:** Add namespaced Overview markup and styles inside the existing single-file frontend, compose the existing pure Profile calculations into a small preview model, and render the preview from the response already fetched by `scheduleStatsWarm()`. Keep a separate Overview tooltip element while reusing the safe structured tooltip renderer, and route the explicit call-to-action through a shared top-level tab activation function.

**Tech Stack:** Python 3.10+, pytest, vanilla JavaScript, HTML/CSS, FastAPI static frontend, Node.js syntax checks.

## Global Constraints

- Modify only `src/tokdash/static/index.html` and `tests/test_profile_stats_frontend.py` during implementation; design and plan documents are already committed.
- Keep the existing five Overview KPIs and two charts in their current order, dimensions, and two-column grid.
- Place the new Profile band after the charts and before the Tools Breakdown table.
- Overview exposes Daily only, with Active days, Current streak, Longest streak, and a `View full profile` action.
- Keep the fixed Profile window explicitly labelled `Past 52 weeks · Daily`; do not imply it follows the Overview date picker.
- Preserve Profile's 52×7 geometry: 364 square daily cells, 3 px gaps, and 2 px corner radius.
- Reuse the existing scheduled `/api/stats` warm request; do not add another endpoint call.
- Do not set `statsLoaded` when only the Overview preview has been populated.
- Do not change backend responses, Profile calculations, Daily/Weekly/Cumulative behavior, calendar cursors, or Profile mode state.
- Use namespaced `overview-profile-*` IDs/classes and bilingual English/Simplified Chinese copy.
- Use existing theme tokens and heat colors only; add no dependency and no hard-coded light-only palette.
- Preserve keyboard focus, structured tooltips, reduced motion, and horizontal scrolling on narrow screens.
- Do not add the separately planned Last Week quick-range preset.
- Never stage or commit `.superpowers/` visual-companion artifacts.

## File Map

- Modify: `src/tokdash/static/index.html`
  - Owns the Overview Profile shell, localized copy, responsive CSS, Daily preview renderer, tooltip routing, warm-response reuse, and navigation.
- Modify: `tests/test_profile_stats_frontend.py`
  - Extends the existing Profile pure-JavaScript harness and adds markup, rendering, request-reuse, and navigation contracts.
- Reference only: `docs/superpowers/specs/2026-07-27-overview-profile-summary-design.md`
  - Approved behavior, hierarchy, error handling, accessibility, and regression boundaries.

---

### Task 1: Add the Overview Profile Shell and Responsive Visual Contract

**Files:**
- Modify: `src/tokdash/static/index.html:447-492,984-1085,2105-2260,2352-2507`
- Test: `tests/test_profile_stats_frontend.py`

**Interfaces:**
- Consumes: existing theme variables, `.surface`, `.profile-activity-cell`, `.profile-activity-tooltip`, `activeDays`, `streak`, `longestStreak`, `less`, and `more` translations.
- Produces: `#overviewProfileSummary`, `#overviewProfileGrid`, `#overviewProfileTooltip`, three metric value IDs, loading/error/ready containers, and `#overviewProfileOpen` for Tasks 2 and 3.

- [ ] **Step 1: Write the failing markup and style contract test**

Append this test before `test_main_inline_script_parses_with_node` in `tests/test_profile_stats_frontend.py`:

```python
def test_overview_profile_summary_markup_and_style_contract():
    source = INDEX_HTML.read_text(encoding="utf-8")
    compact = re.sub(r"\s+", "", source)
    required_ids = [
        "overviewProfileSummary",
        "overviewProfileTitle",
        "overviewProfileOpen",
        "overviewProfileLoading",
        "overviewProfileUnavailable",
        "overviewProfileReady",
        "overviewProfileActiveDays",
        "overviewProfileCurrentStreak",
        "overviewProfileLongestStreak",
        "overviewProfileScroller",
        "overviewProfileGrid",
        "overviewProfileTooltip",
    ]
    for element_id in required_ids:
        assert f'id="{element_id}"' in source

    assert source.index('id="modelChart"') < source.index('id="overviewProfileSummary"')
    assert source.index('id="overviewProfileSummary"') < source.index('id="toolsTable"')
    for key in [
        "overviewProfileEyebrow",
        "overviewProfileTitle",
        "overviewProfileRange",
        "viewFullProfile",
        "overviewProfileUnavailable",
    ]:
        assert source.count(f"{key}: '") == 2

    assert ".overview-profile-band{" in compact
    assert "grid-template-columns:minmax(180px,220px)minmax(0,1fr)" in compact
    assert ".overview-profile-grid{" in compact
    assert "grid-template-columns:repeat(52,minmax(8px,1fr))" in compact
    assert "gap:3px" in compact
    assert ".overview-profile-cell{border-radius:2px" in compact
    assert "@media(max-width:800px)" in compact
    assert ".overview-profile-cell{transform:none!important;}" in compact
```

- [ ] **Step 2: Run the contract test to verify it fails**

Run:

```bash
python -m pytest tests/test_profile_stats_frontend.py::test_overview_profile_summary_markup_and_style_contract -q
```

Expected: FAIL because `overviewProfileSummary` and the namespaced styles do not exist.

- [ ] **Step 3: Add bilingual copy**

Add these keys near the existing Profile translations in both language dictionaries:

```javascript
// English
overviewProfileEyebrow: 'Profile activity',
overviewProfileTitle: 'Your year in tokens',
overviewProfileRange: 'Past 52 weeks · Daily',
viewFullProfile: 'View full profile',
overviewProfileUnavailable: 'Profile activity is temporarily unavailable.',

// Simplified Chinese
overviewProfileEyebrow: 'Profile 活动',
overviewProfileTitle: '你的 Token 年度足迹',
overviewProfileRange: '过去 52 周 · 每日',
viewFullProfile: '查看完整 Profile',
overviewProfileUnavailable: 'Profile 活动暂时不可用。',
```

- [ ] **Step 4: Add the Profile band markup after the charts section**

Insert this immediately after the closing `</section>` for the two Overview charts and before `<!-- Tables -->`:

```html
<section id="overviewProfileSummary" class="surface overview-profile-band mb-6" data-state="loading" aria-labelledby="overviewProfileTitle" aria-busy="true">
  <div class="overview-profile-copy">
    <div class="overview-profile-eyebrow" data-i18n="overviewProfileEyebrow">Profile activity</div>
    <h2 id="overviewProfileTitle" data-i18n="overviewProfileTitle">Your year in tokens</h2>
    <p data-i18n="overviewProfileRange">Past 52 weeks · Daily</p>
    <button id="overviewProfileOpen" class="overview-profile-open" type="button">
      <span data-i18n="viewFullProfile">View full profile</span>
      <span aria-hidden="true">→</span>
    </button>
  </div>
  <div class="overview-profile-main">
    <div id="overviewProfileLoading" class="overview-profile-state overview-profile-loading" aria-live="polite">
      <span class="sr-only" data-i18n="loading">Loading…</span>
      <div class="overview-profile-skeleton-metrics" aria-hidden="true"><i></i><i></i><i></i></div>
      <div class="overview-profile-skeleton-grid" aria-hidden="true"></div>
    </div>
    <div id="overviewProfileUnavailable" class="overview-profile-state overview-profile-unavailable" data-i18n="overviewProfileUnavailable">Profile activity is temporarily unavailable.</div>
    <div id="overviewProfileReady" class="overview-profile-ready">
      <dl class="overview-profile-metrics">
        <div data-tone="cost"><dd id="overviewProfileActiveDays">—</dd><dt data-i18n="activeDays">Active Days</dt></div>
        <div data-tone="cta"><dd id="overviewProfileCurrentStreak">—</dd><dt data-i18n="streak">Streak</dt></div>
        <div data-tone="primary"><dd id="overviewProfileLongestStreak">—</dd><dt data-i18n="longestStreak">Longest Streak</dt></div>
      </dl>
      <div class="overview-profile-heat-head">
        <span data-i18n="dailyActivity">Daily Activity</span>
        <span><span data-i18n="less">Less</span> · <span data-i18n="more">More</span></span>
      </div>
      <div id="overviewProfileScroller" class="overview-profile-scroll">
        <div id="overviewProfileGrid" class="overview-profile-grid" role="grid" aria-label="Token activity"></div>
      </div>
    </div>
  </div>
  <div id="overviewProfileTooltip" class="profile-activity-tooltip overview-profile-tooltip" role="tooltip" hidden></div>
</section>
```

- [ ] **Step 5: Add namespaced, theme-derived styles**

Add this block immediately after the existing Profile activity CSS:

```css
.overview-profile-band{display:grid;grid-template-columns:minmax(180px,220px) minmax(0,1fr);gap:20px;align-items:stretch;min-height:128px;padding:16px 18px;border-color:color-mix(in srgb,var(--color-primary) 18%,var(--color-border));background:linear-gradient(105deg,var(--color-surface-glass),color-mix(in srgb,var(--color-primary) 7%,var(--color-surface-glass)));box-shadow:0 10px 28px color-mix(in srgb,var(--color-primary) 6%,transparent);}
.overview-profile-copy{display:flex;flex-direction:column;justify-content:center;padding-right:18px;border-right:1px solid color-mix(in srgb,var(--color-primary) 16%,var(--color-border));}
.overview-profile-eyebrow{color:var(--color-primary);font-size:10px;font-weight:850;letter-spacing:.08em;text-transform:uppercase;}
.overview-profile-copy h2{margin-top:5px;font-size:15px;font-weight:850;}
.overview-profile-copy p{margin-top:2px;color:var(--color-muted);font-size:11px;}
.overview-profile-open{display:inline-flex;align-items:center;gap:5px;width:max-content;margin-top:11px;border:0;background:transparent;color:var(--color-primary);font:inherit;font-size:11px;font-weight:800;cursor:pointer;}
.overview-profile-open:is(:hover,:focus-visible){text-decoration:underline;text-underline-offset:3px;}
.overview-profile-open:focus-visible{outline:2px solid color-mix(in srgb,var(--color-primary) 52%,transparent);outline-offset:3px;border-radius:4px;}
.overview-profile-main{display:flex;min-width:0;align-items:center;}
.overview-profile-state,.overview-profile-ready{width:100%;}
.overview-profile-band:not([data-state="loading"]) .overview-profile-loading,.overview-profile-band:not([data-state="error"]) .overview-profile-unavailable,.overview-profile-band:not([data-state="ready"]) .overview-profile-ready{display:none;}
.overview-profile-skeleton-metrics{display:flex;gap:18px;margin-bottom:12px;}.overview-profile-skeleton-metrics i{display:block;width:82px;height:20px;border-radius:6px;background:color-mix(in srgb,var(--color-border) 72%,transparent);}
.overview-profile-skeleton-grid{height:57px;border-radius:4px;background:linear-gradient(90deg,color-mix(in srgb,var(--color-border) 58%,transparent),color-mix(in srgb,var(--color-primary) 10%,var(--color-border)),color-mix(in srgb,var(--color-border) 58%,transparent));background-size:200% 100%;animation:overview-profile-pulse 1.4s ease-in-out infinite;}
@keyframes overview-profile-pulse{50%{background-position:100% 0;}}
.overview-profile-unavailable{color:var(--color-muted);font-size:12px;}
.overview-profile-metrics{display:flex;align-items:baseline;gap:18px;margin-bottom:10px;}
.overview-profile-metrics>div{--overview-profile-tone:var(--color-primary);display:flex;align-items:baseline;gap:5px;}.overview-profile-metrics>div[data-tone="cost"]{--overview-profile-tone:var(--color-cost);}.overview-profile-metrics>div[data-tone="cta"]{--overview-profile-tone:var(--color-cta);}
.overview-profile-metrics dd{margin:0;color:var(--overview-profile-tone);font-size:15px;font-weight:850;font-variant-numeric:tabular-nums;}.overview-profile-metrics dt{color:var(--color-muted);font-size:10px;white-space:nowrap;}
.overview-profile-heat-head{display:flex;justify-content:space-between;margin-bottom:6px;color:var(--color-muted);font-size:10px;}
.overview-profile-scroll{overflow-x:auto;padding:2px 0 4px;}
.overview-profile-grid{display:grid;grid-auto-flow:column;grid-template-columns:repeat(52,minmax(8px,1fr));grid-template-rows:repeat(7,minmax(8px,1fr));gap:3px;min-width:572px;width:100%;}
.overview-profile-cell{border-radius:2px;}
@media(max-width:800px){.overview-profile-band{grid-template-columns:1fr;gap:14px;}.overview-profile-copy{padding:0 0 12px;border-right:0;border-bottom:1px solid color-mix(in srgb,var(--color-primary) 16%,var(--color-border));}.overview-profile-metrics{flex-wrap:wrap;}}
@media(prefers-reduced-motion:reduce){.overview-profile-skeleton-grid{animation:none;}.overview-profile-cell{transform:none!important;}}
```

- [ ] **Step 6: Run the markup contract and full Profile file**

Run:

```bash
python -m pytest tests/test_profile_stats_frontend.py::test_overview_profile_summary_markup_and_style_contract -q
python -m pytest tests/test_profile_stats_frontend.py -q
```

Expected: the new contract passes; the complete file reports `11 passed`.

- [ ] **Step 7: Commit the shell**

```bash
git add src/tokdash/static/index.html tests/test_profile_stats_frontend.py
git commit -m "feat: add overview profile summary shell"
```

---

### Task 2: Render Daily Activity from the Existing Stats Warm Response

**Files:**
- Modify: `src/tokdash/static/index.html:3449-3480,5850-6345`
- Test: `tests/test_profile_stats_frontend.py`

**Interfaces:**
- Consumes: `getProfileActivityWindow(contributions, today, weekCount = 52)`, `summarizeProfileActivity(days)`, `groupProfileActivityWeeks(days)`, `buildProfileActivityCells(mode, days, weeks)`, `getProfileActivityColor(level)`, `formatProfileDayTooltip(day)`, `renderProfileActivityTooltipContent(tooltip, model)`, `bindProfileActivityTooltip(target, model)`, `fillMissingDays(contributions)`, `statsCache.default`, and `isOverviewActive()`.
- Produces:
  - `buildOverviewProfilePreview(contributions: Contribution[], today?: Date) -> {days: Contribution[], summary: ProfileSummary, cells: ProfileDailyCell[]}`.
  - `setOverviewProfileState(state: 'loading'|'ready'|'error') -> void`.
  - `renderOverviewProfilePreview(contributions?: Contribution[]) -> void`.
  - `resolveProfileActivityTooltip(target?: HTMLElement) -> HTMLElement|null`, while preserving all existing tooltip function signatures.

- [ ] **Step 1: Extend the pure-JavaScript harness and write the failing model test**

Add this signature to `PROFILE_FUNCTIONS` after `buildProfileActivityCells`:

```python
"function buildOverviewProfilePreview(contributions, today = new Date()) {",
```

Add this test after the existing default-window test:

```python
@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_overview_profile_preview_uses_daily_52_week_model(tmp_path: Path):
    payload = {
        "today": "2026-07-27",
        "days": [_day("2026-07-26", 25), _day("2026-07-27", 75)],
    }
    result = _run_profile_js(
        tmp_path,
        "buildOverviewProfilePreview(payload.days, new Date(`${payload.today}T12:00:00`))",
        payload,
    )
    assert len(result["days"]) == 364
    assert len(result["cells"]) == 364
    assert result["summary"]["recordedTokens"] == 100
    assert result["summary"]["activeDays"] == 2
    assert result["summary"]["currentStreak"] == 2
    assert result["summary"]["longestStreak"] == 2
    assert result["cells"][-1]["level"] == 4
```

- [ ] **Step 2: Write the failing renderer and warm-request reuse contract**

Add:

```python
def test_overview_profile_renderer_reuses_stats_warm_response():
    source = INDEX_HTML.read_text(encoding="utf-8")
    warm = _extract_js_function(source, "function scheduleStatsWarm() {")
    renderer = _extract_js_function(
        source, "function renderOverviewProfilePreview(contributions = statsCache.default) {"
    )
    resolver = _extract_js_function(
        source, "function resolveProfileActivityTooltip(target) {"
    )

    assert warm.count("fetchJsonWithRetry(appPath('/api/stats')") == 1
    assert "fillMissingDays(data.contributions || [])" in warm
    assert "statsCache.default = filledContributions;" in warm
    assert "renderOverviewProfilePreview(filledContributions);" in warm
    assert "setOverviewProfileState('error');" in warm
    assert "fetch(" not in renderer
    assert "buildOverviewProfilePreview(contributions" in renderer
    assert "overviewProfileTooltip" in renderer
    assert "bindProfileActivityTooltip(cell, tooltip);" in renderer
    assert "target?.dataset.profileTooltipId || 'profileActivityTooltip'" in resolver
    assert "renderOverviewProfilePreview();" in _extract_js_function(
        source, "function renderOverviewTab(data) {"
    )
```

- [ ] **Step 3: Run both new tests to verify they fail**

Run:

```bash
python -m pytest \
  tests/test_profile_stats_frontend.py::test_overview_profile_preview_uses_daily_52_week_model \
  tests/test_profile_stats_frontend.py::test_overview_profile_renderer_reuses_stats_warm_response -q
```

Expected: both FAIL because the preview model, renderer, and warm-response hydration do not exist.

- [ ] **Step 4: Add the pure preview model**

Add immediately after `buildProfileActivityCells`:

```javascript
function buildOverviewProfilePreview(contributions, today = new Date()) {
  const days = getProfileActivityWindow(contributions || [], today);
  const weeks = groupProfileActivityWeeks(days);
  return {
    days,
    summary: summarizeProfileActivity(days),
    cells: buildProfileActivityCells('daily', days, weeks).cells,
  };
}
```

- [ ] **Step 5: Route shared tooltip functions to the target's namespaced tooltip**

Add before `showProfileActivityTooltip`, then replace the first line of both `showProfileActivityTooltip` and `hideProfileActivityTooltip` as shown. Keep their signatures and `bindProfileActivityTooltip(target, model)` unchanged so the complete Profile view stays source-compatible:

```javascript
function resolveProfileActivityTooltip(target) {
  const tooltipId = target?.dataset.profileTooltipId || 'profileActivityTooltip';
  return document.getElementById(tooltipId);
}

function showProfileActivityTooltip(target, model) {
  const tooltip = resolveProfileActivityTooltip(target);
  if (!tooltip || !target || !model?.title) return;
  renderProfileActivityTooltipContent(tooltip, model);
  tooltip.hidden = false;
  target.setAttribute('aria-describedby', tooltip.id);
  const rect = target.getBoundingClientRect();
  const gap = 8;
  const left = Math.max(gap, Math.min(
    window.innerWidth - tooltip.offsetWidth - gap,
    rect.left + (rect.width - tooltip.offsetWidth) / 2,
  ));
  let top = rect.top - tooltip.offsetHeight - gap;
  if (top < gap) top = Math.min(window.innerHeight - tooltip.offsetHeight - gap, rect.bottom + gap);
  tooltip.style.left = `${left}px`;
  tooltip.style.top = `${Math.max(gap, top)}px`;
}

function hideProfileActivityTooltip(target) {
  const tooltip = resolveProfileActivityTooltip(target);
  if (tooltip) tooltip.hidden = true;
  if (target) target.removeAttribute('aria-describedby');
}
```

- [ ] **Step 6: Add loading/error state and Daily DOM rendering**

Add after `renderProfileView` and before `setProfileActivityMode`:

```javascript
let overviewProfileDidInitialScroll = false;

function setOverviewProfileState(state) {
  const shell = document.getElementById('overviewProfileSummary');
  if (!shell) return;
  shell.dataset.state = state;
  shell.setAttribute('aria-busy', String(state === 'loading'));
}

function ensureOverviewProfileInitialScroll() {
  if (overviewProfileDidInitialScroll) return;
  const scroller = document.getElementById('overviewProfileScroller');
  if (scroller && scroller.scrollWidth > scroller.clientWidth) {
    scroller.scrollLeft = scroller.scrollWidth;
    overviewProfileDidInitialScroll = true;
  }
}

function renderOverviewProfilePreview(contributions = statsCache.default) {
  const grid = document.getElementById('overviewProfileGrid');
  if (!grid) return;
  if (!Array.isArray(contributions)) {
    setOverviewProfileState('loading');
    return;
  }

  const { summary, cells } = buildOverviewProfilePreview(contributions, new Date());
  document.getElementById('overviewProfileActiveDays').textContent = formatNumber(summary.activeDays || 0);
  document.getElementById('overviewProfileCurrentStreak').textContent = pluralDays(summary.currentStreak || 0);
  document.getElementById('overviewProfileLongestStreak').textContent = pluralDays(summary.longestStreak || 0);
  grid.style.setProperty('--profile-activity-empty', getProfileActivityColor(0));
  grid.style.setProperty('--profile-activity-strong', getProfileActivityColor(4));
  grid.replaceChildren();

  cells.forEach((definition) => {
    const cell = document.createElement('button');
    cell.type = 'button';
    cell.className = 'profile-activity-cell overview-profile-cell';
    cell.setAttribute('role', 'gridcell');
    cell.style.background = getProfileActivityColor(definition.level);
    if (definition.day.isFuture) {
      cell.disabled = true;
      cell.setAttribute('aria-hidden', 'true');
    } else {
      cell.dataset.profileTooltipId = 'overviewProfileTooltip';
      const tooltip = formatProfileDayTooltip(definition.day);
      bindProfileActivityTooltip(cell, tooltip);
    }
    grid.appendChild(cell);
  });

  setOverviewProfileState('ready');
  requestAnimationFrame(ensureOverviewProfileInitialScroll);
}
```

- [ ] **Step 7: Render cached data with Overview and hydrate it from `scheduleStatsWarm()`**

Add this final line to `renderOverviewTab(data)` after its deferred table scheduling:

```javascript
renderOverviewProfilePreview();
```

Replace `scheduleStatsWarm()` with:

```javascript
function scheduleStatsWarm() {
  if (statsWarmScheduled || statsLoaded) return;
  statsWarmScheduled = true;
  setTimeout(() => {
    scheduleIdle(() => {
      fetchJsonWithRetry(appPath('/api/stats'), {}, { attempts: 2, baseDelayMs: 600 })
        .then((data) => {
          const filledContributions = fillMissingDays(data.contributions || []);
          statsCache.default = filledContributions;
          if (isOverviewActive()) renderOverviewProfilePreview(filledContributions);
        })
        .catch(() => {
          statsWarmScheduled = false;
          if (isOverviewActive()) setOverviewProfileState('error');
        });
    }, 1500);
  }, 750);
}
```

This changes only how the already-scheduled response is consumed. It does not add a fetch, set `statsLoaded`, or hydrate hidden Stats controls.

- [ ] **Step 8: Update the existing visual-polish contract for tooltip routing**

In `test_profile_visual_polish_contract`, retain the existing renderer/binder assertions and add:

```python
    resolver = _extract_js_function(
        source, "function resolveProfileActivityTooltip(target) {"
    )
    assert "dataset.profileTooltipId" in resolver
    assert "profileActivityTooltip" in resolver
```

- [ ] **Step 9: Run focused tests and the main-script parser**

Run:

```bash
python -m pytest tests/test_profile_stats_frontend.py -q
```

Expected: `13 passed`, including Node parsing and both new renderer tests.

- [ ] **Step 10: Commit Daily rendering**

```bash
git add src/tokdash/static/index.html tests/test_profile_stats_frontend.py
git commit -m "feat: render profile summary on overview"
```

---

### Task 3: Add Explicit Navigation into the Complete Profile View

**Files:**
- Modify: `src/tokdash/static/index.html:5808-5824,7530-7545`
- Test: `tests/test_profile_stats_frontend.py`

**Interfaces:**
- Consumes: the current top-level tab activation behavior, `loadStats()`, `renderOverviewTab(data)`, `ensureSessionsLoaded()`, `loadQuota()`, `loadPricingDb()`, and `setView('profile')`.
- Produces:
  - `activateDashboardTab(tab: 'overview'|'sessions'|'stats'|'quota'|'pricing') -> void`.
  - `openOverviewProfile() -> void`.
  - A click binding from `#overviewProfileOpen` to `openOverviewProfile`.

- [ ] **Step 1: Write the failing navigation contract**

Add:

```python
def test_overview_profile_navigation_preserves_profile_state_contract():
    source = INDEX_HTML.read_text(encoding="utf-8")
    activator = _extract_js_function(source, "function activateDashboardTab(tab) {")
    opener = _extract_js_function(source, "function openOverviewProfile() {")

    assert "document.getElementById(`${tab}-content`).classList.add('active');" in activator
    assert "if (tab === 'stats') loadStats();" in activator
    assert "activateDashboardTab('stats');" in opener
    assert "setView('profile');" in opener
    assert "profileActivityMode =" not in opener
    assert "monthCursor =" not in opener
    assert "yearCursor =" not in opener
    assert "addEventListener('click', openOverviewProfile)" in source
```

- [ ] **Step 2: Run it to verify it fails**

Run:

```bash
python -m pytest tests/test_profile_stats_frontend.py::test_overview_profile_navigation_preserves_profile_state_contract -q
```

Expected: FAIL because top-level tab activation is still embedded directly in each click listener.

- [ ] **Step 3: Extract top-level tab activation and add the Profile opener**

Replace the existing `// Tabs` listener block with:

```javascript
function activateDashboardTab(tab) {
  const button = document.querySelector(`.tab-btn[data-tab="${tab}"]`);
  const content = document.getElementById(`${tab}-content`);
  if (!button || !content) return;

  document.querySelectorAll('.tab-btn').forEach((item) => item.setAttribute('aria-selected', 'false'));
  button.setAttribute('aria-selected', 'true');
  document.querySelectorAll('.tab-content').forEach((item) => item.classList.remove('active'));
  content.classList.add('active');

  if (tab !== 'overview') {
    const tooltip = document.getElementById('overviewProfileTooltip');
    if (tooltip) tooltip.hidden = true;
  }
  if (tab === 'stats') loadStats();
  if (tab === 'overview' && lastUsageResponse) renderOverviewTab(lastUsageResponse);
  if (tab === 'sessions') ensureSessionsLoaded();
  if (tab === 'quota' && !quotaLoaded) loadQuota();
  if (tab === 'pricing' && !pricingDbLoaded) loadPricingDb();
}

function openOverviewProfile() {
  activateDashboardTab('stats');
  setView('profile');
}

document.querySelectorAll('.tab-btn').forEach((button) => {
  button.addEventListener('click', () => activateDashboardTab(button.dataset.tab));
});
```

This extraction preserves every existing top-level tab side effect. `setView('profile')` changes only `calendarState.view`, so the Month/Year cursors and the previously selected Profile activity mode remain untouched.

- [ ] **Step 4: Bind the explicit Overview action**

Add beside the existing Profile/Stats event bindings:

```javascript
document.getElementById('overviewProfileOpen')?.addEventListener('click', openOverviewProfile);
```

- [ ] **Step 5: Run the navigation, Profile, and syntax tests**

Run:

```bash
python -m pytest \
  tests/test_profile_stats_frontend.py::test_overview_profile_navigation_preserves_profile_state_contract \
  tests/test_profile_stats_frontend.py::test_profile_view_html_and_localization_contract \
  tests/test_profile_stats_frontend.py::test_main_inline_script_parses_with_node -q
python -m pytest tests/test_profile_stats_frontend.py -q
```

Expected: the three selected tests pass, then the complete file reports `14 passed`.

- [ ] **Step 6: Commit navigation**

```bash
git add src/tokdash/static/index.html tests/test_profile_stats_frontend.py
git commit -m "feat: link overview summary to profile"
```

---

### Task 4: Verify Compatibility, Performance, and the Local Preview

**Files:**
- Modify only if verification exposes a defect: `src/tokdash/static/index.html`, `tests/test_profile_stats_frontend.py`

**Interfaces:**
- Consumes: the complete Overview Profile summary from Tasks 1–3.
- Produces: a verified local preview ready for user approval; no push or pull request.

- [ ] **Step 1: Run focused and repository-wide automated checks**

Run:

```bash
python -m pytest tests/test_profile_stats_frontend.py -q
python -m compileall -q src tests
git diff --check
python -m pytest -q
```

Expected:

- Profile frontend: `14 passed`.
- Compileall and diff check: exit 0 with no output.
- Full suite: all new tests pass. The pre-existing host-timezone baseline may remain as the only failure: `tests/test_period_semantics.py::test_previous_period_range_month_uses_full_previous_calendar_month`; verify it separately with `TZ=UTC`.

- [ ] **Step 2: Check for configured lint and type-check commands**

Run:

```bash
rg -n "mypy|pyright|typecheck|ruff|eslint|lint" pyproject.toml package.json Makefile tox.ini 2>/dev/null || true
```

Expected in the current repository: no configured Python/JavaScript type-check or lint target. Report that explicitly; do not invent an unconfigured command.

- [ ] **Step 3: Start or reuse the local Tokdash server and verify health**

Use the repository's existing local launch command/session. Verify:

```bash
curl -fsS http://127.0.0.1:55424/api/health
```

Expected: HTTP 200 and the Tokdash health payload. If the prior server no longer reflects the new checkout, stop only that known process/session and restart Tokdash on an explicitly verified free port; do not terminate unrelated processes.

- [ ] **Step 4: Inspect the visual hierarchy in the browser**

Verify on Overview:

1. The five KPI cards and two charts retain their previous widths and order.
2. The Profile band appears only after the charts and before Tools Breakdown.
3. The fixed 52-week label makes its date semantics distinct from the date picker.
4. The shell does not cause a large layout jump when background Stats data resolves.
5. Exactly 364 Daily cells render and the most recent edge is visible on overflow.
6. Active days and both streak metrics match Stats → Profile.

- [ ] **Step 5: Inspect interaction, accessibility, and responsive states**

Verify:

1. Hover and keyboard focus show the colored structured tooltip in English and Chinese.
2. Tooltip positioning stays inside the viewport near both horizontal edges.
3. Light and dark mode remain legible in at least Paper and the default style theme.
4. At wide desktop width the band is two columns and at ≤800 px it stacks.
5. Narrow layouts retain square cells and horizontal scrolling instead of shrinking the grid.
6. Reduced-motion mode removes the skeleton animation and cell transform.
7. `View full profile` activates Stats → Profile without changing its Daily/Weekly/Cumulative mode or Month/Year cursors.
8. Returning to Overview leaves charts and tables intact.

- [ ] **Step 6: If verification finds a defect, add one regression test before the smallest fix**

Run the new regression test alone and confirm it fails, make the minimal correction, then rerun Steps 1–5. Commit only the defect and its test:

```bash
git add src/tokdash/static/index.html tests/test_profile_stats_frontend.py
git commit -m "fix: stabilize overview profile summary"
```

- [ ] **Step 7: Hand off the local preview**

Report:

- local URL;
- the three implementation commits;
- focused/full-suite/type-check/lint results;
- the known timezone baseline if it remains;
- functional impact and regression risks checked;
- confirmation that `.superpowers/` was not staged;
- confirmation that nothing was pushed and no pull request was opened.
