# Overview Profile Modes and Token Milestones Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add synchronized Daily, Weekly, and Cumulative controls to the Overview Profile band and apply four Tier Aura token milestones consistently across Overview and the complete Profile view.

**Architecture:** Keep the feature frontend-only in the existing embedded `index.html`. Extend the current pure Profile activity model with deterministic milestone metadata, reuse that metadata in the structured tooltip and both renderers, and keep `profileActivityMode` as the single page-session state. Overview retains a separate namespaced renderer and aggregate hit-target layer while sharing calculations, tooltip construction, and milestone semantics with Profile.

**Tech Stack:** HTML/CSS, vanilla browser JavaScript embedded in `src/tokdash/static/index.html`, Python 3.10+ pytest harnesses, Node.js for extracted JavaScript and whole-script syntax checks, existing FastAPI/Uvicorn local server.

## Global Constraints

- Implement only the approved behavior in `docs/superpowers/specs/2026-07-27-overview-profile-modes-milestones-design.md`.
- Modify only `src/tokdash/static/index.html` and `tests/test_profile_stats_frontend.py` during feature implementation; the design and plan documents are already committed.
- Stay on the current normal branch `feat/profile-stats-view`; do not create a linked worktree.
- Never delete files. Do not stage or commit `.superpowers/` visual-companion artifacts.
- Keep one in-memory `profileActivityMode` shared by Overview and Profile; page reload still defaults to Daily and adds no persistence.
- Daily classifies the day's tokens, Weekly classifies the week's tokens, and Cumulative classifies the running total through the week.
- Thresholds are inclusive: 100,000,000; 300,000,000; 500,000,000; and 1,000,000,000 tokens.
- Preserve the 52×7 geometry, square cells, 3 px gaps, 2 px corner radius, current heat-level calculation, aggregate height calculation, and Monday-to-Sunday grouping.
- Preserve the base heat colors. Milestones add rings, glow, and tooltip emphasis; they do not replace the underlying data encoding.
- Overview uses a quieter resting aura than Profile. Daily decorates the qualifying day cell; Weekly/Cumulative decorate the top active cell and strengthen the whole column on hover/focus.
- Reuse the existing scheduled `/api/stats` warm response; switching modes must not fetch data or change backend contracts.
- Preserve loading, error, empty, retry, initial-scroll, language, theme, pointer/keyboard parity, viewport-aware tooltip positioning, and reduced-motion behavior.
- Use safe tooltip DOM construction with `createElement`, `textContent`, and `replaceChildren`; do not interpolate usage data through `innerHTML`.
- Do not implement the separate Last Week quick-range preset in this branch or plan.
- Before handoff, run the focused frontend tests, CI compile command, full pytest suite, whole-script Node syntax test, and configured type-check/lint discovery. Report the exact command and diagnostics for any existing failure; if no static type checker is configured, report that explicitly.
- Call out these intended behavior changes in the handoff: Overview gains three modes, Overview/Profile share the mode, the fixed Daily subtitle is removed, and qualifying units gain milestone treatment.

## File Map

- Modify: `src/tokdash/static/index.html`
  - Owns milestone classification, activity-cell metadata, tooltip model/rendering, Tier Aura CSS, Overview controls and hit targets, synchronized state, and both activity renderers.
- Modify: `tests/test_profile_stats_frontend.py`
  - Extends the existing pytest-to-Node harness with milestone boundary and aggregation tests, tooltip-model tests, markup/style contracts, state synchronization contracts, and shipped-script syntax coverage.
- Reference only: `docs/superpowers/specs/2026-07-27-overview-profile-modes-milestones-design.md`
  - Approved thresholds, visual direction, accessibility, compatibility, and regression boundaries.
- Reference only: `docs/superpowers/specs/2026-07-27-overview-profile-summary-design.md`
  - Existing Overview placement, warm-cache ownership, loading/error behavior, and compact hierarchy.

---

### Task 1: Add Pure Milestone Classification and Mode-Aware Activity Models

**Files:**
- Modify: `tests/test_profile_stats_frontend.py:17-47, 129-303`
- Modify: `src/tokdash/static/index.html:6080-6160`

**Interfaces:**
- Consumes: `safeProfileNumber(value)`, `profileDayTokens(day)`, `buildProfileActivitySeries(mode, weeks)`, `getProfileDailyLevel(value, peak)`, and `getProfileAggregateHeight(value, peak)`.
- Produces:
  - `getProfileMilestoneTier(value) -> null | {level: 1|2|3|4, minTokens: number, label: '100M+'|'300M+'|'500M+'|'1B+', tone: 'milestone-1'|'milestone-2'|'milestone-3'|'milestone-4'}`.
  - Daily cell definitions with `value` and `milestone`.
  - Weekly/Cumulative cell definitions with `isCap` and cap-only `milestone`.
  - `buildOverviewProfilePreview(contributions, today = new Date(), mode = 'daily') -> {mode, days, weeks, summary, cells, series}`.

- [ ] **Step 1: Extend the extracted-function harness and write the failing milestone test**

Add the milestone helper signature before `buildProfileActivityCells` and update the Overview builder signature in `PROFILE_FUNCTIONS`:

```python
PROFILE_FUNCTIONS = [
    "function parseDateKey(value) {",
    "function formatDateKey(date) {",
    "function startOfWeekMonday(date) {",
    "function createEmptyContribution(key) {",
    "function safeProfileNumber(value) {",
    "function getProfileActivityWindow(contributions, today, weekCount = 52) {",
    "function profileDayTokens(day) {",
    "function summarizeProfileActivity(days) {",
    "function groupProfileActivityWeeks(days) {",
    "function buildProfileActivitySeries(mode, weeks) {",
    "function getProfileDailyLevel(value, peak) {",
    "function getProfileAggregateHeight(value, peak) {",
    "function getProfileMilestoneTier(value) {",
    "function buildProfileActivityCells(mode, days, weeks) {",
    "function buildOverviewProfilePreview(contributions, today = new Date(), mode = 'daily') {",
]
```

Add this test after `test_profile_week_and_cumulative_cells_follow_seven_level_scale`:

```python
@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_profile_milestones_are_inclusive_and_enrich_each_mode(tmp_path: Path):
    payload = {
        "today": "2026-01-11",
        "values": [
            -1,
            0,
            99_999_999,
            100_000_000,
            299_999_999,
            300_000_000,
            499_999_999,
            500_000_000,
            999_999_999,
            1_000_000_000,
        ],
        "days": [
            _day("2025-12-29", 100_000_000),
            _day("2026-01-05", 250_000_000),
        ],
    }
    expression = """
    (() => {
      const today = new Date(`${payload.today}T12:00:00`);
      const days = getProfileActivityWindow(payload.days, today, 2);
      const weeks = groupProfileActivityWeeks(days);
      const daily = buildProfileActivityCells('daily', days, weeks);
      const weekly = buildProfileActivityCells('weekly', days, weeks);
      const cumulative = buildProfileActivityCells('cumulative', days, weeks);
      const compactCaps = (result) => result.cells
        .filter((cell) => cell.isCap)
        .map((cell) => ({
          value: cell.value,
          milestone: cell.milestone?.level || null,
        }));
      return {
        tiers: payload.values.map((value) => getProfileMilestoneTier(value)?.level || null),
        labels: payload.values.map((value) => getProfileMilestoneTier(value)?.label || null),
        dailyMilestones: daily.cells
          .filter((cell) => cell.milestone)
          .map((cell) => ({date: cell.day.date, level: cell.milestone.level})),
        weeklyCaps: compactCaps(weekly),
        cumulativeCaps: compactCaps(cumulative),
        weeklyNonCapMilestones: weekly.cells.filter(
          (cell) => !cell.isCap && cell.milestone,
        ).length,
        previewMode: buildOverviewProfilePreview(payload.days, today, 'weekly').mode,
      };
    })()
    """
    result = _run_profile_js(tmp_path, expression, payload)

    assert result["tiers"] == [None, None, None, 1, 1, 2, 2, 3, 3, 4]
    assert result["labels"][3::2] == ["100M+", "300M+", "500M+", "1B+"]
    assert result["dailyMilestones"] == [
        {"date": "2025-12-29", "level": 1},
        {"date": "2026-01-05", "level": 1},
    ]
    assert result["weeklyCaps"] == [
        {"value": 100_000_000, "milestone": 1},
        {"value": 250_000_000, "milestone": 1},
    ]
    assert result["cumulativeCaps"] == [
        {"value": 100_000_000, "milestone": 1},
        {"value": 350_000_000, "milestone": 2},
    ]
    assert result["weeklyNonCapMilestones"] == 0
    assert result["previewMode"] == "weekly"
```

- [ ] **Step 2: Run the new test and verify the intended failure**

Run:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest \
  tests/test_profile_stats_frontend.py::test_profile_milestones_are_inclusive_and_enrich_each_mode -q
```

Expected: FAIL because `getProfileMilestoneTier` and the mode-aware Overview builder signature do not exist.

- [ ] **Step 3: Implement the pure milestone helper**

Add immediately before `buildProfileActivityCells`:

```javascript
function getProfileMilestoneTier(value) {
  const safeValue = Math.max(0, safeProfileNumber(value));
  const tiers = [
    { level: 4, minTokens: 1_000_000_000, label: '1B+', tone: 'milestone-4' },
    { level: 3, minTokens: 500_000_000, label: '500M+', tone: 'milestone-3' },
    { level: 2, minTokens: 300_000_000, label: '300M+', tone: 'milestone-2' },
    { level: 1, minTokens: 100_000_000, label: '100M+', tone: 'milestone-1' },
  ];
  return tiers.find((tier) => safeValue >= tier.minTokens) || null;
}
```

- [ ] **Step 4: Enrich Daily, Weekly, and Cumulative cell definitions**

Replace `buildProfileActivityCells` with:

```javascript
function buildProfileActivityCells(mode, days, weeks) {
  if (mode === 'daily') {
    const peak = Math.max(0, ...(days || []).map(profileDayTokens));
    return {
      series: [],
      cells: (days || []).map((day, index) => {
        const value = profileDayTokens(day);
        return {
          index,
          day,
          value,
          level: getProfileDailyLevel(value, peak),
          active: value > 0,
          milestone: day.isFuture ? null : getProfileMilestoneTier(value),
        };
      }),
    };
  }
  const series = buildProfileActivitySeries(mode, weeks || []);
  const peak = Math.max(0, ...series.map((week) => safeProfileNumber(week?.totals?.tokens)));
  const cells = series.flatMap((week, weekIndex) => {
    const value = safeProfileNumber(week?.totals?.tokens);
    const height = getProfileAggregateHeight(value, peak);
    const milestone = getProfileMilestoneTier(value);
    return Array.from({ length: 7 }, (_, row) => {
      const active = 7 - row <= height;
      const isCap = active && row === 7 - height;
      return {
        weekIndex,
        row,
        active,
        isCap,
        value,
        milestone: isCap ? milestone : null,
      };
    });
  });
  return { cells, series };
}
```

- [ ] **Step 5: Make the Overview preview builder mode-aware without breaking its Daily default**

Replace the existing Overview builder with:

```javascript
function buildOverviewProfilePreview(contributions, today = new Date(), mode = 'daily') {
  const days = getProfileActivityWindow(contributions || [], today);
  const weeks = groupProfileActivityWeeks(days);
  const activity = buildProfileActivityCells(mode, days, weeks);
  return {
    mode,
    days,
    weeks,
    summary: summarizeProfileActivity(days),
    cells: activity.cells,
    series: activity.series,
  };
}
```

- [ ] **Step 6: Run the pure-model tests**

Run:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest \
  tests/test_profile_stats_frontend.py::test_profile_milestones_are_inclusive_and_enrich_each_mode \
  tests/test_profile_stats_frontend.py::test_profile_week_and_cumulative_cells_follow_seven_level_scale \
  tests/test_profile_stats_frontend.py::test_overview_profile_preview_uses_daily_52_week_model -q
```

Expected: all three tests PASS. The existing Overview test proves the default remains Daily.

- [ ] **Step 7: Commit the pure model**

```bash
git add src/tokdash/static/index.html tests/test_profile_stats_frontend.py
git commit -m "feat: classify profile token milestones"
```

---

### Task 2: Add Milestone Tooltip Metadata and Tier Aura to Profile

**Files:**
- Modify: `tests/test_profile_stats_frontend.py:48-127, 304-470`
- Modify: `src/tokdash/static/index.html:460-494, 2170-2560, 6170-6395`

**Interfaces:**
- Consumes: `getProfileMilestoneTier(value)` and enriched cell definitions from Task 1.
- Produces:
  - `formatProfileAggregateTooltip(...) -> {title, rows, milestone, accessibleText}`.
  - `applyProfileMilestone(target, milestone) -> void` using `data-milestone` only.
  - Safe tooltip header badge markup and tier-colored total row.
  - Profile Daily and aggregate Tier Aura hooks for Task 3 to reuse in Overview.

- [ ] **Step 1: Update the tooltip harness and write the failing milestone-tooltip test**

Add `milestone` to `TOOLTIP_JS_SETUP` and extract the milestone helper:

```python
TOOLTIP_JS_SETUP = """
const LABELS = {
  cumulative: 'Cumulative', total: 'Total', tokensUnit: 'tokens',
  input: 'Input', output: 'Output', cacheRead: 'Cache read',
  cacheWrite: 'Cache write', reasoning: 'Reasoning',
  estimatedCost: 'Estimated cost', milestone: 'Milestone',
};
function t(key) { return LABELS[key] || key; }
function formatNumber(value) { return new Intl.NumberFormat('en-US').format(Number(value) || 0); }
function formatCurrency(value) { return `$${(Number(value) || 0).toFixed(2)}`; }
function formatShortDate(value) { return value || '—'; }
"""
```

Change the extracted function list inside `_run_profile_tooltip_js` to:

```python
functions = "\n".join(
    [
        _extract_js_function(source, "function safeProfileNumber(value) {"),
        _extract_js_function(source, "function getProfileMilestoneTier(value) {"),
        _extract_js_function(
            source,
            "function formatProfileAggregateTooltip(aggregate, cumulative = false) {",
        ),
    ]
)
```

Add this test after the existing tooltip-model tests:

```python
@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_profile_tooltip_exposes_milestone_badge_tone_and_accessible_text(
    tmp_path: Path,
):
    payload = {
        "high": {
            "startDate": "2026-07-20",
            "endDate": "2026-07-26",
            "totals": {"tokens": 1_000_000_000, "cost": 12.5},
            "tokenBreakdown": {
                "input": 400_000_000,
                "output": 300_000_000,
                "cacheRead": 200_000_000,
                "cacheWrite": 100_000_000,
                "reasoning": 0,
            },
        },
        "normal": {
            "startDate": "2026-07-27",
            "endDate": "2026-07-27",
            "totals": {"tokens": 99_999_999, "cost": 1.0},
            "tokenBreakdown": {},
        },
    }
    result = _run_profile_tooltip_js(
        tmp_path,
        "({ high: formatProfileAggregateTooltip(payload.high), normal: formatProfileAggregateTooltip(payload.normal) })",
        payload,
    )

    assert result["high"]["milestone"] == {
        "level": 4,
        "minTokens": 1_000_000_000,
        "label": "1B+",
        "tone": "milestone-4",
    }
    assert result["high"]["rows"][0]["tone"] == "milestone-4"
    assert "Milestone: 1B+" in result["high"]["accessibleText"]
    assert result["normal"]["milestone"] is None
    assert result["normal"]["rows"][0]["tone"] == "primary"
    assert "Milestone:" not in result["normal"]["accessibleText"]
```

- [ ] **Step 2: Write the failing safe-rendering and Tier Aura contract test**

Add:

```python
def test_profile_milestone_tooltip_and_tier_aura_contract():
    source = INDEX_HTML.read_text(encoding="utf-8")
    compact = re.sub(r"\s+", "", source)
    formatter = _extract_js_function(
        source,
        "function formatProfileAggregateTooltip(aggregate, cumulative = false) {",
    )
    renderer = _extract_js_function(
        source,
        "function renderProfileActivityTooltipContent(tooltip, model) {",
    )
    profile_renderer = _extract_js_function(source, "function renderProfileView() {")

    assert "milestone: 'Milestone'" in source
    assert "milestone: '里程碑'" in source
    assert "getProfileMilestoneTier(tokenTotal)" in formatter
    assert "profile-activity-tooltip-badge" in renderer
    assert "badge.textContent = model.milestone.label;" in renderer
    assert "tooltip.dataset.milestone" in renderer
    assert ".innerHTML" not in renderer
    assert "applyProfileMilestone(cell, definition.milestone);" in profile_renderer
    assert "applyProfileMilestone(hit, milestone);" in profile_renderer
    for level in range(1, 5):
        assert f'--profile-milestone-{level}:' in compact
        assert f'[data-milestone="{level}"]' in source
        assert f'[data-tone="milestone-{level}"]' in source
    assert "prefers-reduced-motion:reduce" in compact
```

- [ ] **Step 3: Run both tests and verify they fail**

Run:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest \
  tests/test_profile_stats_frontend.py::test_profile_tooltip_exposes_milestone_badge_tone_and_accessible_text \
  tests/test_profile_stats_frontend.py::test_profile_milestone_tooltip_and_tier_aura_contract -q
```

Expected: both FAIL because milestone tooltip metadata, badge DOM, renderer hooks, and Tier Aura CSS do not exist.

- [ ] **Step 4: Add the localized accessible milestone noun**

Add near the existing Profile tooltip translations:

```javascript
// English dictionary
milestone: 'Milestone',

// Simplified Chinese dictionary
milestone: '里程碑',
```

- [ ] **Step 5: Enrich the tooltip model while preserving non-milestone output**

In `formatProfileAggregateTooltip`, calculate metadata before `definitions` and use it for the Total row:

```javascript
const tokenTotal = safeProfileNumber(aggregate?.totals?.tokens);
const milestone = getProfileMilestoneTier(tokenTotal);
const definitions = [
  {
    key: 'total',
    label: t('total'),
    value: `${formatNumber(tokenTotal)} ${t('tokensUnit')}`,
    tone: milestone?.tone || 'primary',
    prominent: true,
  },
  { key: 'input', label: t('input'), value: formatNumber(safeProfileNumber(breakdown.input)), tone: 'primary', prominent: false },
  { key: 'output', label: t('output'), value: formatNumber(safeProfileNumber(breakdown.output)), tone: 'secondary', prominent: false },
  { key: 'cacheRead', label: t('cacheRead'), value: formatNumber(safeProfileNumber(breakdown.cacheRead)), tone: 'cost', prominent: false },
  { key: 'cacheWrite', label: t('cacheWrite'), value: formatNumber(safeProfileNumber(breakdown.cacheWrite)), tone: 'cta', prominent: false },
  {
    key: 'reasoning',
    label: t('reasoning'),
    value: formatNumber(safeProfileNumber(breakdown.reasoning)),
    tone: 'reasoning',
    prominent: false,
    include: safeProfileNumber(breakdown.reasoning) > 0,
  },
  {
    key: 'estimatedCost',
    label: t('estimatedCost'),
    value: formatCurrency(safeProfileNumber(aggregate?.totals?.cost)),
    tone: 'cost',
    prominent: false,
  },
];
const rows = definitions
  .filter((row) => row.include !== false)
  .map(({ include, ...row }) => row);
const accessibleText = [
  title,
  milestone ? `${t('milestone')}: ${milestone.label}` : '',
  ...rows.map((row) => `${row.label}: ${row.value}`),
].filter(Boolean).join('. ');
return { title, rows, milestone, accessibleText };
```

- [ ] **Step 6: Add safe badge DOM to the shared tooltip renderer**

Replace the header construction at the top of `renderProfileActivityTooltipContent` with:

```javascript
const header = document.createElement('div');
header.className = 'profile-activity-tooltip-header';
const headerTitle = document.createElement('span');
headerTitle.className = 'profile-activity-tooltip-title';
headerTitle.textContent = model.title;
header.appendChild(headerTitle);
if (model.milestone) {
  const badge = document.createElement('span');
  badge.className = 'profile-activity-tooltip-badge';
  badge.dataset.milestone = String(model.milestone.level);
  badge.textContent = model.milestone.label;
  header.appendChild(badge);
  tooltip.dataset.milestone = String(model.milestone.level);
} else {
  delete tooltip.dataset.milestone;
}
```

Leave the existing row loop and final `tooltip.replaceChildren(header, body)` unchanged.

- [ ] **Step 7: Add the reusable milestone DOM hook and apply it in Profile**

Add before `renderProfileView`:

```javascript
function applyProfileMilestone(target, milestone) {
  if (!target || !milestone) return;
  target.dataset.milestone = String(milestone.level);
}
```

In the Daily branch of `renderProfileView`, apply the tier only for non-future days before binding the tooltip:

```javascript
} else {
  applyProfileMilestone(cell, definition.milestone);
  const tooltip = formatProfileDayTooltip(definition.day);
  bindProfileActivityTooltip(cell, tooltip);
}
```

In the aggregate visual-cell branch, apply cap metadata after setting `is-aggregate`:

```javascript
cell.dataset.weekIndex = String(definition.weekIndex);
cell.classList.toggle('is-aggregate', definition.active);
applyProfileMilestone(cell, definition.milestone);
```

In the aggregate hit-target loop, add:

```javascript
const milestone = getProfileMilestoneTier(aggregate?.totals?.tokens);
applyProfileMilestone(hit, milestone);
```

Place it after `hit.className = 'profile-activity-week-hit';` and before tooltip binding.

- [ ] **Step 8: Add the Tier Aura and tooltip badge CSS**

Add after the existing Profile tooltip and cell-interaction styles:

```css
.profile-activity-shell,.overview-profile-band{--profile-milestone-1:#06b6d4;--profile-milestone-2:#8b5cf6;--profile-milestone-3:#f59e0b;--profile-milestone-4:#ec4899;}
.profile-activity-cell[data-milestone="1"],.profile-activity-week-hit[data-milestone="1"],.profile-activity-tooltip-badge[data-milestone="1"]{--profile-milestone-tone:var(--profile-milestone-1);}
.profile-activity-cell[data-milestone="2"],.profile-activity-week-hit[data-milestone="2"],.profile-activity-tooltip-badge[data-milestone="2"]{--profile-milestone-tone:var(--profile-milestone-2);}
.profile-activity-cell[data-milestone="3"],.profile-activity-week-hit[data-milestone="3"],.profile-activity-tooltip-badge[data-milestone="3"]{--profile-milestone-tone:var(--profile-milestone-3);}
.profile-activity-cell[data-milestone="4"],.profile-activity-week-hit[data-milestone="4"],.profile-activity-tooltip-badge[data-milestone="4"]{--profile-milestone-tone:var(--profile-milestone-4);}
.profile-activity-cell[data-milestone="1"]{box-shadow:0 0 0 1px color-mix(in srgb,var(--profile-milestone-tone) 66%,transparent);}
.profile-activity-cell[data-milestone="2"]{box-shadow:0 0 0 1px color-mix(in srgb,var(--profile-milestone-tone) 72%,transparent),0 0 7px color-mix(in srgb,var(--profile-milestone-tone) 34%,transparent);}
.profile-activity-cell[data-milestone="3"]{box-shadow:0 0 0 1px color-mix(in srgb,var(--profile-milestone-tone) 82%,transparent),0 0 0 2px color-mix(in srgb,var(--profile-milestone-tone) 22%,transparent),0 0 10px color-mix(in srgb,var(--profile-milestone-tone) 44%,transparent);}
.profile-activity-cell[data-milestone="4"]{box-shadow:0 0 0 1px color-mix(in srgb,var(--color-text) 74%,transparent),0 0 0 3px color-mix(in srgb,var(--profile-milestone-tone) 38%,transparent),0 0 14px color-mix(in srgb,var(--profile-milestone-tone) 58%,transparent);}
button.profile-activity-cell[data-milestone]:not(:disabled):is(:hover,:focus-visible),.profile-activity-cell[data-milestone].is-column-hover{box-shadow:0 0 0 1px color-mix(in srgb,var(--color-text) 82%,transparent),0 0 0 3px color-mix(in srgb,var(--profile-milestone-tone) 48%,transparent),0 0 18px color-mix(in srgb,var(--profile-milestone-tone) 68%,transparent);}
.profile-activity-week-hit[data-milestone]:focus-visible{outline-color:var(--profile-milestone-tone);box-shadow:0 0 12px color-mix(in srgb,var(--profile-milestone-tone) 24%,transparent);}
.profile-activity-tooltip-header{display:flex;align-items:center;justify-content:space-between;gap:8px;}
.profile-activity-tooltip-title{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.profile-activity-tooltip-badge{flex:0 0 auto;padding:2px 6px;border:1px solid color-mix(in srgb,var(--profile-milestone-tone) 48%,transparent);border-radius:999px;background:color-mix(in srgb,var(--profile-milestone-tone) 13%,transparent);color:var(--profile-milestone-tone);box-shadow:0 0 10px color-mix(in srgb,var(--profile-milestone-tone) 22%,transparent);font-size:9px;font-weight:900;letter-spacing:.04em;}
.profile-activity-tooltip-row[data-tone="milestone-1"]{--profile-tooltip-tone:var(--profile-milestone-1);}
.profile-activity-tooltip-row[data-tone="milestone-2"]{--profile-tooltip-tone:var(--profile-milestone-2);}
.profile-activity-tooltip-row[data-tone="milestone-3"]{--profile-tooltip-tone:var(--profile-milestone-3);}
.profile-activity-tooltip-row[data-tone="milestone-4"]{--profile-tooltip-tone:var(--profile-milestone-4);}
.overview-profile-cell[data-milestone="2"]{box-shadow:0 0 0 1px color-mix(in srgb,var(--profile-milestone-tone) 66%,transparent),0 0 5px color-mix(in srgb,var(--profile-milestone-tone) 22%,transparent);}
.overview-profile-cell[data-milestone="3"]{box-shadow:0 0 0 1px color-mix(in srgb,var(--profile-milestone-tone) 76%,transparent),0 0 0 2px color-mix(in srgb,var(--profile-milestone-tone) 18%,transparent),0 0 7px color-mix(in srgb,var(--profile-milestone-tone) 30%,transparent);}
.overview-profile-cell[data-milestone="4"]{box-shadow:0 0 0 1px color-mix(in srgb,var(--color-text) 68%,transparent),0 0 0 2px color-mix(in srgb,var(--profile-milestone-tone) 30%,transparent),0 0 9px color-mix(in srgb,var(--profile-milestone-tone) 42%,transparent);}
@media(prefers-reduced-motion:reduce){button.profile-activity-cell[data-milestone]:not(:disabled):is(:hover,:focus-visible){transform:none;transition:none;}}
```

During browser verification, tune only percentages—not tier names, thresholds, geometry, or semantic colors—to maintain contrast across themes.

- [ ] **Step 9: Run the tooltip, visual-contract, and shipped-script tests**

Run:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest \
  tests/test_profile_stats_frontend.py::test_profile_tooltip_exposes_milestone_badge_tone_and_accessible_text \
  tests/test_profile_stats_frontend.py::test_profile_milestone_tooltip_and_tier_aura_contract \
  tests/test_profile_stats_frontend.py::test_profile_tooltip_model_has_semantic_rows_and_accessible_text \
  tests/test_profile_stats_frontend.py::test_profile_tooltip_keeps_zero_rows_and_omits_zero_reasoning \
  tests/test_profile_stats_frontend.py::test_profile_visual_polish_contract \
  tests/test_profile_stats_frontend.py::test_main_inline_script_parses_with_node -q
```

Expected: all listed tests PASS, including the unchanged non-milestone tooltip cases and whole-script `node --check` coverage.

- [ ] **Step 10: Commit Profile milestone presentation**

```bash
git add src/tokdash/static/index.html tests/test_profile_stats_frontend.py
git commit -m "feat: highlight profile token milestones"
```

---

### Task 3: Add Overview Mode Controls, Aggregate Rendering, and Shared State

**Files:**
- Modify: `tests/test_profile_stats_frontend.py:472-575`
- Modify: `src/tokdash/static/index.html:494-518, 1066-1098, 2280-2555, 6315-6460, 7701-7712`

**Interfaces:**
- Consumes: `buildOverviewProfilePreview(..., mode)`, `applyProfileMilestone`, `formatProfileAggregateTooltip`, `bindProfileActivityTooltip`, `profileActivityMode`, and the existing cached contributions.
- Produces:
  - `#overviewProfileModeDaily`, `#overviewProfileModeWeekly`, `#overviewProfileModeCumulative`.
  - `#overviewProfileGridWrap` and `#overviewProfileWeekHits`.
  - `setOverviewProfileColumnHover(weekIndex, active) -> void`.
  - `syncProfileActivityModeControls() -> void`.
  - Mode-aware `renderOverviewProfilePreview(contributions = statsCache.default) -> void`.

- [ ] **Step 1: Write the failing Overview markup/style contract additions**

Extend `required_ids` in `test_overview_profile_summary_markup_and_style_contract` with:

```python
"overviewProfileModeDaily",
"overviewProfileModeWeekly",
"overviewProfileModeCumulative",
"overviewProfileGridWrap",
"overviewProfileWeekHits",
```

Add these assertions to that test:

```python
assert "overviewProfileRange: 'Past 52 weeks'" in source
assert "overviewProfileRange: '过去 52 周'" in source
assert source.count('class="profile-activity-mode overview-profile-mode"') == 3
assert ".overview-profile-grid-wrap{" in compact
assert ".overview-profile-mode{" in compact
assert 'id="overviewProfileWeekHits"' in source
```

- [ ] **Step 2: Write the failing shared-state and aggregate-renderer contract test**

Add before `test_overview_profile_navigation_preserves_profile_state_contract`:

```python
def test_overview_profile_modes_share_state_and_render_aggregate_hits_contract():
    source = INDEX_HTML.read_text(encoding="utf-8")
    overview_renderer = _extract_js_function(
        source,
        "function renderOverviewProfilePreview(contributions = statsCache.default) {",
    )
    profile_renderer = _extract_js_function(source, "function renderProfileView() {")
    setter = _extract_js_function(source, "function setProfileActivityMode(mode) {")
    syncer = _extract_js_function(
        source,
        "function syncProfileActivityModeControls() {",
    )

    assert "buildOverviewProfilePreview(contributions, new Date(), profileActivityMode)" in overview_renderer
    assert "profileActivityMode === 'daily' ? 'button' : 'span'" in overview_renderer
    assert "overviewProfileWeekHits" in overview_renderer
    assert "formatProfileAggregateTooltip(aggregate, profileActivityMode === 'cumulative')" in overview_renderer
    assert "setOverviewProfileColumnHover(weekIndex, true)" in overview_renderer
    assert "applyProfileMilestone(hit, milestone);" in overview_renderer
    assert "fetch(" not in overview_renderer
    assert "syncProfileActivityModeControls();" in overview_renderer
    assert "syncProfileActivityModeControls();" in profile_renderer
    assert "syncProfileActivityModeControls();" in setter
    assert "if (isOverviewActive()) renderOverviewProfilePreview();" in setter
    assert "fetch(" not in setter
    for element_id in [
        "profileModeDaily",
        "profileModeWeekly",
        "profileModeCumulative",
        "overviewProfileModeDaily",
        "overviewProfileModeWeekly",
        "overviewProfileModeCumulative",
    ]:
        assert element_id in syncer
    for element_id in [
        "overviewProfileModeDaily",
        "overviewProfileModeWeekly",
        "overviewProfileModeCumulative",
    ]:
        assert f"document.getElementById('{element_id}').addEventListener" in source
```

- [ ] **Step 3: Run both tests and verify they fail**

Run:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest \
  tests/test_profile_stats_frontend.py::test_overview_profile_summary_markup_and_style_contract \
  tests/test_profile_stats_frontend.py::test_overview_profile_modes_share_state_and_render_aggregate_hits_contract -q
```

Expected: FAIL because Overview still contains only the Daily grid and has no namespaced controls or hit-target layer.

- [ ] **Step 4: Update the Overview range translations**

Replace the two existing values:

```javascript
// English
overviewProfileRange: 'Past 52 weeks',

// Simplified Chinese
overviewProfileRange: '过去 52 周',
```

- [ ] **Step 5: Replace the Overview heatmap header and grid wrapper markup**

Replace the current `overview-profile-heat-head` and scroller content with:

```html
<div class="overview-profile-heat-head">
  <span data-i18n="tokenActivity">Token activity</span>
  <div class="overview-profile-modes" role="group" aria-label="Activity aggregation">
    <button id="overviewProfileModeDaily" class="profile-activity-mode overview-profile-mode" type="button" aria-pressed="true" data-i18n="daily">Daily</button>
    <button id="overviewProfileModeWeekly" class="profile-activity-mode overview-profile-mode" type="button" aria-pressed="false" data-i18n="weekly">Weekly</button>
    <button id="overviewProfileModeCumulative" class="profile-activity-mode overview-profile-mode" type="button" aria-pressed="false" data-i18n="cumulative">Cumulative</button>
  </div>
</div>
<div id="overviewProfileScroller" class="overview-profile-scroll">
  <div id="overviewProfileGridWrap" class="overview-profile-grid-wrap">
    <div id="overviewProfileGrid" class="overview-profile-grid" role="grid" aria-label="Token activity"></div>
    <div id="overviewProfileWeekHits" class="profile-activity-week-hits overview-profile-week-hits" hidden></div>
  </div>
</div>
```

Also change the visible range paragraph to:

```html
<p data-i18n="overviewProfileRange">Past 52 weeks</p>
```

- [ ] **Step 6: Add compact control, wrapper, and responsive styles**

Replace the existing heat-head/grid rules with:

```css
.overview-profile-heat-head{display:flex;align-items:center;gap:10px;margin-bottom:6px;color:var(--color-muted);font-size:10px;}
.overview-profile-heat-head>span{margin-right:auto;}
.overview-profile-modes{display:flex;align-items:center;gap:2px;}
.overview-profile-mode{padding:4px 7px;font-size:10px;}
.overview-profile-scroll{overflow-x:auto;padding:2px 0 4px;}
.overview-profile-grid-wrap{position:relative;min-width:572px;}
.overview-profile-grid{display:grid;grid-auto-flow:column;grid-template-columns:repeat(52,minmax(8px,1fr));grid-template-rows:repeat(7,minmax(8px,1fr));gap:3px;width:100%;}
.overview-profile-week-hits{grid-template-columns:repeat(52,minmax(8px,1fr));gap:3px;}
.overview-profile-cell{border-radius:2px;}
@media(max-width:800px){.overview-profile-band{grid-template-columns:1fr;gap:14px;}.overview-profile-copy{padding:0 0 12px;border-right:0;border-bottom:1px solid color-mix(in srgb,var(--color-primary) 16%,var(--color-border));}.overview-profile-metrics{flex-wrap:wrap;}.overview-profile-heat-head{align-items:flex-start;flex-wrap:wrap;}.overview-profile-modes{margin-left:auto;}}
```

Keep the existing reduced-motion rule.

- [ ] **Step 7: Add Overview column hover and shared button-state helpers**

Add before `ensureOverviewProfileInitialScroll`:

```javascript
function setOverviewProfileColumnHover(weekIndex, active) {
  document.querySelectorAll(`#overviewProfileGrid [data-week-index="${weekIndex}"]`).forEach((cell) => {
    cell.classList.toggle('is-column-hover', active);
  });
}

function syncProfileActivityModeControls() {
  const controls = {
    daily: ['profileModeDaily', 'overviewProfileModeDaily'],
    weekly: ['profileModeWeekly', 'overviewProfileModeWeekly'],
    cumulative: ['profileModeCumulative', 'overviewProfileModeCumulative'],
  };
  Object.entries(controls).forEach(([mode, ids]) => {
    ids.forEach((id) => {
      document.getElementById(id)?.setAttribute(
        'aria-pressed',
        String(profileActivityMode === mode),
      );
    });
  });
}
```

Replace the three-button loop at the bottom of `renderProfileView` with:

```javascript
syncProfileActivityModeControls();
```

- [ ] **Step 8: Replace the Overview renderer with the mode-aware implementation**

Replace `renderOverviewProfilePreview` with:

```javascript
function renderOverviewProfilePreview(contributions = statsCache.default) {
  const grid = document.getElementById('overviewProfileGrid');
  const hits = document.getElementById('overviewProfileWeekHits');
  if (!grid || !hits) return;
  syncProfileActivityModeControls();
  if (!Array.isArray(contributions)) {
    const shell = document.getElementById('overviewProfileSummary');
    if (shell?.dataset.state !== 'error') setOverviewProfileState('loading');
    return;
  }

  const { summary, cells, series } = buildOverviewProfilePreview(
    contributions,
    new Date(),
    profileActivityMode,
  );
  document.getElementById('overviewProfileActiveDays').textContent = formatNumber(summary.activeDays || 0);
  document.getElementById('overviewProfileCurrentStreak').textContent = pluralDays(summary.currentStreak || 0);
  document.getElementById('overviewProfileLongestStreak').textContent = pluralDays(summary.longestStreak || 0);
  grid.style.setProperty('--profile-activity-empty', getProfileActivityColor(0));
  grid.style.setProperty('--profile-activity-strong', getProfileActivityColor(4));
  document.getElementById('overviewProfileTooltip').hidden = true;
  grid.replaceChildren();
  hits.replaceChildren();

  cells.forEach((definition) => {
    const cell = document.createElement(profileActivityMode === 'daily' ? 'button' : 'span');
    cell.className = 'profile-activity-cell overview-profile-cell';
    cell.setAttribute('role', 'gridcell');
    if (profileActivityMode === 'daily') {
      cell.type = 'button';
      cell.style.background = getProfileActivityColor(definition.level);
      if (definition.day.isFuture) {
        cell.disabled = true;
        cell.setAttribute('aria-hidden', 'true');
      } else {
        applyProfileMilestone(cell, definition.milestone);
        cell.dataset.profileTooltipId = 'overviewProfileTooltip';
        const tooltip = formatProfileDayTooltip(definition.day);
        bindProfileActivityTooltip(cell, tooltip);
      }
    } else {
      cell.dataset.weekIndex = String(definition.weekIndex);
      cell.classList.toggle('is-aggregate', definition.active);
      applyProfileMilestone(cell, definition.milestone);
    }
    grid.appendChild(cell);
  });

  hits.hidden = profileActivityMode === 'daily';
  if (profileActivityMode !== 'daily') {
    series.forEach((aggregate, weekIndex) => {
      const hit = document.createElement('button');
      const milestone = getProfileMilestoneTier(aggregate?.totals?.tokens);
      const tooltip = formatProfileAggregateTooltip(
        aggregate,
        profileActivityMode === 'cumulative',
      );
      hit.type = 'button';
      hit.className = 'profile-activity-week-hit';
      hit.dataset.profileTooltipId = 'overviewProfileTooltip';
      applyProfileMilestone(hit, milestone);
      bindProfileActivityTooltip(hit, tooltip);
      hit.addEventListener('mouseenter', () => setOverviewProfileColumnHover(weekIndex, true));
      hit.addEventListener('mouseleave', () => setOverviewProfileColumnHover(weekIndex, false));
      hit.addEventListener('focus', () => setOverviewProfileColumnHover(weekIndex, true));
      hit.addEventListener('blur', () => setOverviewProfileColumnHover(weekIndex, false));
      hits.appendChild(hit);
    });
  }

  syncProfileActivityModeControls();
  setOverviewProfileState('ready');
  requestAnimationFrame(ensureOverviewProfileInitialScroll);
}
```

- [ ] **Step 9: Synchronize state changes and wire the Overview buttons**

Replace `setProfileActivityMode` with:

```javascript
function setProfileActivityMode(mode) {
  if (!['daily', 'weekly', 'cumulative'].includes(mode)) return;
  profileActivityMode = mode;
  syncProfileActivityModeControls();
  if (calendarState.view === 'profile' && statsLoaded) renderProfileView();
  if (isOverviewActive()) renderOverviewProfilePreview();
}
```

Add alongside the existing Profile mode listeners:

```javascript
document.getElementById('overviewProfileModeDaily').addEventListener('click', () => setProfileActivityMode('daily'));
document.getElementById('overviewProfileModeWeekly').addEventListener('click', () => setProfileActivityMode('weekly'));
document.getElementById('overviewProfileModeCumulative').addEventListener('click', () => setProfileActivityMode('cumulative'));
```

- [ ] **Step 10: Run the Overview and synchronization tests**

Run:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest \
  tests/test_profile_stats_frontend.py::test_overview_profile_summary_markup_and_style_contract \
  tests/test_profile_stats_frontend.py::test_overview_profile_modes_share_state_and_render_aggregate_hits_contract \
  tests/test_profile_stats_frontend.py::test_overview_profile_renderer_reuses_stats_warm_response \
  tests/test_profile_stats_frontend.py::test_overview_profile_navigation_preserves_profile_state_contract \
  tests/test_profile_stats_frontend.py::test_overview_profile_resize_rearms_initial_scroll_contract \
  tests/test_profile_stats_frontend.py::test_main_inline_script_parses_with_node -q
```

Expected: all listed tests PASS. The warm-response test must still find exactly one `/api/stats` request and no fetch in the Overview renderer.

- [ ] **Step 11: Commit synchronized Overview modes**

```bash
git add src/tokdash/static/index.html tests/test_profile_stats_frontend.py
git commit -m "feat: switch profile activity modes from overview"
```

---

### Task 4: Regression, Type-Check Discovery, and Local Visual Verification

**Files:**
- Modify only if a verified defect is found: `src/tokdash/static/index.html`, `tests/test_profile_stats_frontend.py`

**Interfaces:**
- Consumes: the complete implementation from Tasks 1-3.
- Produces: a verified local build, exact command results, browser evidence for the user, and a clean implementation diff ready for PR review.

- [ ] **Step 1: Run the complete focused frontend file**

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest tests/test_profile_stats_frontend.py -q
```

Expected: all Profile frontend tests PASS. This includes extracted pure JavaScript and the complete shipped inline-script `node --check` test.

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

Expected: PASS. If an unrelated baseline failure remains, record the exact test name and traceback and confirm the focused file still passes.

- [ ] **Step 4: Perform the required type-check and lint discovery**

```bash
rg -n "\[tool\.(ruff|mypy|pyright)|ruff|mypy|pyright|eslint|typecheck|lint" \
  pyproject.toml requirements-dev.txt .github 2>/dev/null || true
```

Expected for the current repository: no configured Python/JavaScript static type-check or lint target. Report this exact discovery command and result. Do not claim that `compileall` or `node --check` is a type checker; they are the applicable configured syntax checks.

- [ ] **Step 5: Start the local server on the review port**

Run in a persistent terminal:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt \
  tokdash serve --bind 127.0.0.1 --port 55425 --no-open
```

Expected: Uvicorn serves Tokdash at `http://127.0.0.1:55425/`. Keep it running for the user's review; do not replace the already-running installed Tokdash service.

- [ ] **Step 6: Verify Overview and Profile behavior in the local browser**

At `http://127.0.0.1:55425/`, verify:

1. Overview still shows KPIs, the two existing charts, then the compact Profile band, then tables.
2. Daily, Weekly, and Cumulative buttons fit without obscuring the heatmap at wide and narrow widths.
3. All cells remain square with tight GitHub-like spacing and 2 px corners.
4. Switching Overview modes does not issue a new `/api/stats` request.
5. Weekly/Cumulative expose one focusable target per week and highlight the aligned column.
6. Opening the complete Profile preserves the selected mode; switching Profile and returning to Overview preserves it in reverse.
7. A qualifying tier shows the approved Cyan/Violet/Gold/Pink aura, a colored numeric badge, and a tier-colored Total row.
8. Non-qualifying tooltips retain their current layout and tones.
9. Tooltip positioning remains inside the viewport at the newest/rightmost column.
10. English/Chinese and light/dark themes remain legible.
11. Keyboard Tab focus matches pointer hover, and reduced-motion mode removes the lift.
12. Loading, empty, and unavailable Overview states expose no stray aggregate hit targets.

Use the automated boundary tests to verify all four thresholds even if the current local usage data does not naturally contain all four levels. The approved visual companion remains the reference for the four-level appearance; production browser verification must at minimum confirm every tier that exists in the user's real dataset plus the non-tier state.

- [ ] **Step 7: Fix only verified defects test-first**

For each defect found in Step 6:

1. Add the smallest focused assertion to `tests/test_profile_stats_frontend.py`.
2. Run that assertion and confirm it fails for the observed reason.
3. Make the smallest correction in `src/tokdash/static/index.html`.
4. Rerun Steps 1-4.

Commit verified corrections only:

```bash
git add src/tokdash/static/index.html tests/test_profile_stats_frontend.py
git commit -m "fix: refine profile activity milestone interactions"
```

If Step 6 finds no defect, do not create an empty commit.

- [ ] **Step 8: Audit compatibility and working-tree scope**

Run:

```bash
git status --short
git diff --check 6a01f34..HEAD
git diff --stat 6a01f34..HEAD
git diff --name-only 6a01f34..HEAD
```

Expected: the diff since the approved design commit contains this plan plus `src/tokdash/static/index.html` and `tests/test_profile_stats_frontend.py`; `.superpowers/` remains untracked and unstaged. Confirm in the handoff that backend APIs, selected-range KPIs, charts, tables, aggregation math, and default-on-reload Daily behavior remain compatible.

Do not push or open the pull request until the user approves the running local result.
