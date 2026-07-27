# Profile Stats View Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional Profile sub-view to Tokdash Stats with reliable 52-week summary metrics and Daily, Weekly, and Cumulative token-activity grids derived from the existing `/api/stats` payload.

**Architecture:** Keep the feature frontend-only inside the existing `src/tokdash/static/index.html`. Add pure date/aggregation helpers that are independently exercised through the repository's pytest-to-Node pattern, then layer namespaced markup/styles and DOM rendering on top. Extend the current Stats view switch without changing the default Month view or any backend contract.

**Tech Stack:** HTML/CSS, browser JavaScript embedded in `index.html`, Python 3.10+ pytest harnesses, Node.js for extracted JavaScript tests, existing FastAPI/Uvicorn local server.

## Global Constraints

- Do not add or change an API endpoint, database operation, source parser, telemetry call, or provider network call.
- Use the existing `/api/stats` response and `statsCache.default`; switching activity modes must not fetch data.
- Keep Month as the default Stats sub-view and preserve Month, Year, and 3D cursors and behavior.
- Render 52 Monday-to-Sunday columns, seven square cells per column, 3 px gaps, 2 px corners, and a 732 CSS px desktop width cap.
- Use the active Tokdash heatmap palette in light, dark, and custom themes.
- Show only Recorded tokens, Peak day, Active days, Current streak, and Longest streak; do not infer a longest task.
- Keep all new visible text in both existing English and Simplified Chinese dictionaries.
- The Last Week quick-range preset, share card, filters, activity insights, and account/profile management are out of scope.
- Never delete files. Do not add `.superpowers/` visual-companion artifacts to Git.
- Before handoff, run focused tests, the full pytest suite, CI's compile check, and the available frontend syntax check. The repository has no configured Python or JavaScript static type checker; report that explicitly.

---

## File Map

- Modify: `src/tokdash/static/index.html`
  - Owns Profile markup, namespaced styles, English/Chinese strings, pure activity derivation helpers, renderer, and Stats sub-view integration.
- Create: `tests/test_profile_stats_frontend.py`
  - Extracts the shipped helper functions and executes them with Node; also asserts the HTML/localization contract.
- Reference only: `docs/superpowers/specs/2026-07-27-profile-stats-view-design.md`
  - Approved behavior and scope; no further edits expected during implementation.

---

### Task 1: Pure 52-week activity model

**Files:**
- Modify: `src/tokdash/static/index.html:5755-5810`
- Create: `tests/test_profile_stats_frontend.py`

**Interfaces:**
- Consumes: existing `parseDateKey(value)`, `formatDateKey(date)`, `startOfWeekMonday(date)`, and `createEmptyContribution(key)` helpers.
- Produces:
  - `safeProfileNumber(value) -> number`
  - `getProfileActivityWindow(contributions, today, weekCount = 52) -> Contribution[]`
  - `profileDayTokens(day) -> number`
  - `summarizeProfileActivity(days) -> {recordedTokens, peakDay, activeDays, currentStreak, longestStreak}`
  - `groupProfileActivityWeeks(days) -> ProfileWeek[]`
  - `buildProfileActivitySeries(mode, weeks) -> ProfileWeek[]`
  - `getProfileDailyLevel(value, peak) -> 0|1|2|3|4`
  - `getProfileAggregateHeight(value, peak) -> integer 0..7`
  - `buildProfileActivityCells(mode, days, weeks) -> {cells, series}`

- [ ] **Step 1: Create the failing Node-backed tests**

Create `tests/test_profile_stats_frontend.py` with the extraction helper and behavior cases below:

```python
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

import tokdash

INDEX_HTML = Path(tokdash.__file__).parent / "static" / "index.html"


def _extract_js_function(source: str, signature: str) -> str:
    start = source.find(signature)
    assert start != -1, f"{signature} not found in index.html"
    depth = 0
    for index in range(source.find("{", start), len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"unterminated JavaScript function: {signature}")


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
    "function buildProfileActivityCells(mode, days, weeks) {",
]


def _run_profile_js(tmp_path: Path, expression: str, payload: dict) -> object:
    source = INDEX_HTML.read_text(encoding="utf-8")
    functions = "\n".join(_extract_js_function(source, signature) for signature in PROFILE_FUNCTIONS)
    harness = tmp_path / "profile-stats.js"
    harness.write_text(
        functions
        + "\nconst payload = JSON.parse(process.argv[2]);\n"
        + f"const result = {expression};\n"
        + "process.stdout.write(JSON.stringify(result));\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        ["node", str(harness), json.dumps(payload)],
        check=True,
        capture_output=True,
        encoding="utf-8",
    )
    return json.loads(result.stdout)


def _day(date: str, tokens: int, *, cost: float = 0.0) -> dict:
    return {
        "date": date,
        "totals": {"tokens": tokens, "cost": cost, "messages": 0},
        "tokenBreakdown": {
            "input": tokens // 2,
            "output": tokens - tokens // 2,
            "cacheRead": 0,
            "cacheWrite": 0,
            "reasoning": 0,
        },
        "sources": [],
    }


@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_profile_window_is_two_monday_aligned_weeks_and_marks_future(tmp_path: Path):
    payload = {"today": "2026-01-07", "days": [_day("2026-01-06", 20)]}
    result = _run_profile_js(
        tmp_path,
        "getProfileActivityWindow(payload.days, new Date(`${payload.today}T12:00:00`), 2)",
        payload,
    )
    assert len(result) == 14
    assert result[0]["date"] == "2025-12-29"
    assert result[-1]["date"] == "2026-01-11"
    assert sum(bool(day["isFuture"]) for day in result) == 4
    assert next(day for day in result if day["date"] == "2026-01-06")["totals"]["tokens"] == 20


@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_profile_summary_excludes_future_and_calculates_streaks(tmp_path: Path):
    payload = {
        "today": "2026-01-07",
        "days": [
            _day("2025-12-29", 4), _day("2025-12-30", 4), _day("2025-12-31", 4),
            _day("2026-01-01", 4), _day("2026-01-02", 4),
            _day("2026-01-05", 10), _day("2026-01-06", 20), _day("2026-01-07", 30),
            _day("2026-01-08", 999),
        ],
    }
    result = _run_profile_js(
        tmp_path,
        "summarizeProfileActivity(getProfileActivityWindow(payload.days, new Date(`${payload.today}T12:00:00`), 2))",
        payload,
    )
    assert result["recordedTokens"] == 80
    assert result["peakDay"]["date"] == "2026-01-07"
    assert result["activeDays"] == 8
    assert result["currentStreak"] == 3
    assert result["longestStreak"] == 5


@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_profile_week_and_cumulative_cells_follow_seven_level_scale(tmp_path: Path):
    payload = {
        "today": "2026-01-11",
        "days": [_day("2025-12-29", 10), _day("2026-01-05", 30)],
    }
    expression = """
    (() => {
      const days = getProfileActivityWindow(payload.days, new Date(`${payload.today}T12:00:00`), 2);
      const weeks = groupProfileActivityWeeks(days);
      return {
        weeks,
        weekly: buildProfileActivityCells('weekly', days, weeks),
        cumulative: buildProfileActivityCells('cumulative', days, weeks),
        levels: [0, 1, 25, 50, 75, 100].map((value) => getProfileDailyLevel(value, 100)),
      };
    })()
    """
    result = _run_profile_js(tmp_path, expression, payload)
    assert [week["totals"]["tokens"] for week in result["weeks"]] == [10, 30]
    weekly_heights = [
        sum(cell["active"] for cell in result["weekly"]["cells"][offset : offset + 7])
        for offset in (0, 7)
    ]
    cumulative_heights = [
        sum(cell["active"] for cell in result["cumulative"]["cells"][offset : offset + 7])
        for offset in (0, 7)
    ]
    assert weekly_heights == [3, 7]
    assert cumulative_heights == [2, 7]
    assert cumulative_heights == sorted(cumulative_heights)
    assert result["cumulative"]["series"][1]["startDate"] == "2025-12-29"
    assert result["cumulative"]["series"][1]["endDate"] == "2026-01-11"
    assert result["levels"] == [0, 1, 1, 2, 3, 4]


@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_profile_default_window_is_52_weeks_and_empty_or_zero_data_is_safe(tmp_path: Path):
    expression = """
    (() => {
      const days = getProfileActivityWindow(payload.days, new Date(`${payload.today}T12:00:00`));
      const weeks = groupProfileActivityWeeks(days);
      return {
        dayCount: days.length,
        weekCount: weeks.length,
        summary: summarizeProfileActivity(days),
        daily: buildProfileActivityCells('daily', days, weeks),
        weekly: buildProfileActivityCells('weekly', days, weeks),
        cumulative: buildProfileActivityCells('cumulative', days, weeks),
      };
    })()
    """
    for source_days in ([], [_day("2026-01-07", 0)]):
        payload = {"today": "2026-01-07", "days": source_days}
        result = _run_profile_js(tmp_path, expression, payload)
        assert result["dayCount"] == 364
        assert result["weekCount"] == 52
        assert len(result["daily"]["cells"]) == 364
        assert len(result["weekly"]["cells"]) == 364
        assert len(result["cumulative"]["cells"]) == 364
        assert result["summary"] == {
            "recordedTokens": 0,
            "peakDay": None,
            "activeDays": 0,
            "currentStreak": 0,
            "longestStreak": 0,
        }
        assert not any(cell["active"] for cell in result["daily"]["cells"])


@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_profile_week_aggregates_breakdown_and_cost_across_year_boundary(tmp_path: Path):
    first = _day("2025-12-29", 100, cost=1.25)
    first["tokenBreakdown"].update(cacheRead=7, cacheWrite=3, reasoning=2)
    second = _day("2026-01-02", 50, cost=0.75)
    second["tokenBreakdown"].update(cacheRead=5, cacheWrite=1, reasoning=4)
    payload = {"today": "2026-01-04", "days": [first, second]}
    result = _run_profile_js(
        tmp_path,
        "groupProfileActivityWeeks(getProfileActivityWindow(payload.days, new Date(`${payload.today}T12:00:00`), 1))[0]",
        payload,
    )
    assert result["startDate"] == "2025-12-29"
    assert result["endDate"] == "2026-01-04"
    assert result["totals"]["tokens"] == 150
    assert result["totals"]["cost"] == 2
    assert result["tokenBreakdown"] == {
        "input": 75,
        "output": 75,
        "cacheRead": 12,
        "cacheWrite": 4,
        "reasoning": 6,
    }
```

- [ ] **Step 2: Run the focused tests and confirm the intended failure**

Run:

```bash
uv run --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest tests/test_profile_stats_frontend.py -q
```

Expected: five failures identifying `function safeProfileNumber(value) { not found in index.html`.

- [ ] **Step 3: Add the pure implementation below `fillYearDays`**

Add these functions in `src/tokdash/static/index.html` immediately after `fillYearDays`:

```javascript
function safeProfileNumber(value) {
  const number = Number(value ?? 0);
  return Number.isFinite(number) ? Math.max(0, number) : 0;
}

function getProfileActivityWindow(contributions, today, weekCount = 52) {
  const safeToday = today instanceof Date && !isNaN(today.getTime()) ? today : new Date();
  const todayKey = formatDateKey(safeToday);
  const firstMonday = startOfWeekMonday(safeToday);
  firstMonday.setDate(firstMonday.getDate() - (Math.max(1, weekCount) - 1) * 7);
  const contributionMap = new Map(
    (Array.isArray(contributions) ? contributions : []).map((day) => [day.date, day])
  );

  return Array.from({ length: Math.max(1, weekCount) * 7 }, (_, index) => {
    const date = new Date(firstMonday.getFullYear(), firstMonday.getMonth(), firstMonday.getDate());
    date.setDate(date.getDate() + index);
    const key = formatDateKey(date);
    const empty = createEmptyContribution(key);
    const source = contributionMap.get(key) || empty;
    return {
      ...empty,
      ...source,
      totals: { ...empty.totals, ...(source.totals || {}) },
      tokenBreakdown: {
        ...empty.tokenBreakdown,
        ...(source.tokenBreakdown || {}),
      },
      sources: Array.isArray(source.sources) ? source.sources : [],
      isFuture: key > todayKey,
    };
  });
}

function profileDayTokens(day) {
  return day?.isFuture ? 0 : safeProfileNumber(day?.totals?.tokens);
}

function summarizeProfileActivity(days) {
  const visible = (Array.isArray(days) ? days : []).filter((day) => !day?.isFuture);
  const active = visible.map((day) => profileDayTokens(day) > 0);
  const peakDay = visible.reduce((best, day) => {
    if (profileDayTokens(day) <= 0) return best;
    return !best || profileDayTokens(day) > profileDayTokens(best) ? day : best;
  }, null);
  let currentStreak = 0;
  for (let index = active.length - 1; index >= 0 && active[index]; index -= 1) currentStreak += 1;
  let longestStreak = 0;
  let runningStreak = 0;
  active.forEach((isActive) => {
    runningStreak = isActive ? runningStreak + 1 : 0;
    longestStreak = Math.max(longestStreak, runningStreak);
  });
  return {
    recordedTokens: visible.reduce((sum, day) => sum + profileDayTokens(day), 0),
    peakDay,
    activeDays: active.filter(Boolean).length,
    currentStreak,
    longestStreak,
  };
}

function groupProfileActivityWeeks(days) {
  const breakdownKeys = ['input', 'output', 'cacheRead', 'cacheWrite', 'reasoning'];
  const list = Array.isArray(days) ? days : [];
  return Array.from({ length: Math.ceil(list.length / 7) }, (_, weekIndex) => {
    const weekDays = list.slice(weekIndex * 7, weekIndex * 7 + 7);
    const visibleDays = weekDays.filter((day) => !day?.isFuture);
    const tokenBreakdown = Object.fromEntries(breakdownKeys.map((key) => [key, 0]));
    const totals = { tokens: 0, cost: 0, messages: 0 };
    visibleDays.forEach((day) => {
      totals.tokens += safeProfileNumber(day?.totals?.tokens);
      totals.cost += safeProfileNumber(day?.totals?.cost);
      totals.messages += safeProfileNumber(day?.totals?.messages);
      breakdownKeys.forEach((key) => {
        tokenBreakdown[key] += safeProfileNumber(day?.tokenBreakdown?.[key]);
      });
    });
    return {
      weekIndex,
      startDate: weekDays[0]?.date || null,
      endDate: weekDays[6]?.date || weekDays.at(-1)?.date || null,
      totals,
      tokenBreakdown,
      sources: visibleDays.flatMap((day) => day.sources || []),
      isFuture: visibleDays.length === 0,
    };
  });
}

function buildProfileActivitySeries(mode, weeks) {
  if (mode !== 'cumulative') return weeks.map((week) => ({ ...week }));
  const breakdownKeys = ['input', 'output', 'cacheRead', 'cacheWrite', 'reasoning'];
  const runningTotals = { tokens: 0, cost: 0, messages: 0 };
  const runningBreakdown = Object.fromEntries(breakdownKeys.map((key) => [key, 0]));
  return weeks.map((week) => {
    Object.keys(runningTotals).forEach((key) => {
      runningTotals[key] += safeProfileNumber(week?.totals?.[key]);
    });
    breakdownKeys.forEach((key) => {
      runningBreakdown[key] += safeProfileNumber(week?.tokenBreakdown?.[key]);
    });
    return {
      ...week,
      startDate: weeks[0]?.startDate || week.startDate,
      totals: { ...runningTotals },
      tokenBreakdown: { ...runningBreakdown },
    };
  });
}

function getProfileDailyLevel(value, peak) {
  const safeValue = safeProfileNumber(value);
  const safePeak = safeProfileNumber(peak);
  if (safeValue <= 0 || safePeak <= 0) return 0;
  const ratio = safeValue / safePeak;
  if (ratio > 0.75) return 4;
  if (ratio > 0.5) return 3;
  if (ratio > 0.25) return 2;
  return 1;
}

function getProfileAggregateHeight(value, peak) {
  const safeValue = safeProfileNumber(value);
  const safePeak = safeProfileNumber(peak);
  return safeValue <= 0 || safePeak <= 0 ? 0 : Math.max(1, Math.ceil((safeValue / safePeak) * 7));
}

function buildProfileActivityCells(mode, days, weeks) {
  if (mode === 'daily') {
    const peak = Math.max(0, ...(days || []).map(profileDayTokens));
    return {
      series: [],
      cells: (days || []).map((day, index) => ({
        index,
        day,
        level: getProfileDailyLevel(profileDayTokens(day), peak),
        active: profileDayTokens(day) > 0,
      })),
    };
  }
  const series = buildProfileActivitySeries(mode, weeks || []);
  const peak = Math.max(0, ...series.map((week) => safeProfileNumber(week?.totals?.tokens)));
  const cells = series.flatMap((week, weekIndex) => {
    const height = getProfileAggregateHeight(week?.totals?.tokens, peak);
    return Array.from({ length: 7 }, (_, row) => ({
      weekIndex,
      row,
      active: 7 - row <= height,
      value: safeProfileNumber(week?.totals?.tokens),
    }));
  });
  return { cells, series };
}
```

- [ ] **Step 4: Run the focused tests and verify they pass**

Run the command from Step 2.

Expected: `5 passed`.

- [ ] **Step 5: Commit the independently tested data model**

```bash
git add src/tokdash/static/index.html tests/test_profile_stats_frontend.py
git commit -m "feat: derive profile activity statistics"
```

---

### Task 2: Profile shell, theme-aware grid styles, and localization

**Files:**
- Modify: `src/tokdash/static/index.html:420-470, 1411-1665, 1980-2440`
- Modify: `tests/test_profile_stats_frontend.py`

**Interfaces:**
- Consumes: existing Stats buttons/containers, CSS variables, `HEAT_COLORS`, and `data-i18n` processing.
- Produces DOM IDs consumed by Task 3: `statsViewTitle`, `viewProfile`, `statsMetricControls`, `calendarProfileView`, five `profileStat*` nodes, `profileActivityGrid`, `profileActivityWeekHits`, `profileActivityMonths`, `profileActivityScroller`, `profileActivityTooltip`, and three `profileMode*` buttons.

- [ ] **Step 1: Add a failing HTML/localization contract test**

Append:

```python
def test_profile_view_html_and_localization_contract():
    source = INDEX_HTML.read_text(encoding="utf-8")
    required_ids = [
        "statsViewTitle", "viewProfile", "statsMetricControls", "calendarProfileView",
        "profileStatRecordedTokens", "profileStatPeakDay", "profileStatActiveDays",
        "profileStatCurrentStreak", "profileStatLongestStreak",
        "profileActivityGrid", "profileActivityWeekHits", "profileActivityMonths",
        "profileActivityScroller", "profileActivityTooltip", "profileModeDaily", "profileModeWeekly",
        "profileModeCumulative",
    ]
    for element_id in required_ids:
        assert f'id="{element_id}"' in source
    assert source.count("profileView: '") == 2
    assert source.count("recordedTokens: '") == 2
    assert source.count("tokenActivity: '") == 2
    assert ".profile-activity-cell" in source
    assert "border-radius:2px" in source.replace(" ", "")
```

- [ ] **Step 2: Run the contract test and verify it fails**

```bash
uv run --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest tests/test_profile_stats_frontend.py::test_profile_view_html_and_localization_contract -q
```

Expected: FAIL because `viewProfile` is absent.

- [ ] **Step 3: Add namespaced Profile styles**

Insert after the existing year-heatmap CSS:

```css
.profile-activity-shell{max-width:732px;margin:0 auto;}
.profile-activity-summary-scroll{overflow-x:auto;padding-bottom:2px;}
.profile-activity-summary{display:grid;grid-template-columns:repeat(5,minmax(120px,1fr));min-width:600px;border:1px solid var(--color-border);border-radius:16px;overflow:hidden;background:color-mix(in srgb,var(--color-surface-glass) 82%,transparent);}
.profile-activity-stat{position:relative;padding:12px 8px;text-align:center;}
.profile-activity-stat+.profile-activity-stat::before{content:"";position:absolute;left:0;top:14px;bottom:14px;width:1px;background:var(--color-border);}
.profile-activity-stat dd{margin:0;color:var(--color-text);font-weight:800;font-size:15px;}
.profile-activity-stat dt{margin-top:3px;color:var(--color-muted);font-size:12px;white-space:nowrap;}
.profile-activity-head{display:flex;align-items:center;gap:16px;margin:32px 0 12px;}
.profile-activity-head h3{margin-right:auto;font-size:16px;font-weight:800;}
.profile-activity-mode{border:0;padding:0;background:transparent;color:var(--color-muted);font:inherit;cursor:pointer;}
.profile-activity-mode[aria-pressed="true"]{color:var(--color-text);}
.profile-activity-scroll{overflow-x:auto;padding:8px 0 12px;}
.profile-activity-grid-wrap{position:relative;min-width:572px;}
.profile-activity-grid{display:grid;grid-auto-flow:column;grid-template-columns:repeat(52,minmax(8px,1fr));grid-template-rows:repeat(7,minmax(8px,1fr));gap:3px;width:100%;}
.profile-activity-cell{width:100%;aspect-ratio:1;border:0;border-radius:2px;background:var(--profile-activity-empty,var(--color-border));padding:0;position:relative;}
button.profile-activity-cell{cursor:pointer;}
.profile-activity-cell.is-aggregate{background:var(--profile-activity-strong,var(--color-primary));}
.profile-activity-cell.is-column-hover.is-aggregate{filter:brightness(1.12);box-shadow:0 0 0 1px color-mix(in srgb,var(--profile-activity-strong,var(--color-primary)) 55%,transparent);}
.profile-activity-cell.is-column-hover:not(.is-aggregate){background:color-mix(in srgb,var(--color-primary) 14%,var(--color-border));}
.profile-activity-week-hits{position:absolute;inset:0;display:grid;grid-template-columns:repeat(52,minmax(8px,1fr));gap:3px;pointer-events:none;}
.profile-activity-week-hit{position:relative;min-width:8px;border:0;background:transparent;padding:0;pointer-events:auto;cursor:pointer;}
.profile-activity-tooltip{position:fixed;z-index:120;max-width:280px;padding:7px 9px;border:1px solid var(--color-border);border-radius:8px;background:var(--color-surface-glass);color:var(--color-text);box-shadow:var(--shadow-md);white-space:pre-line;text-align:left;font-size:11px;line-height:1.35;pointer-events:none;}
.profile-activity-tooltip[hidden]{display:none;}
.profile-activity-months{display:flex;justify-content:space-between;min-width:572px;margin-top:8px;color:var(--color-muted);font-size:12px;}
@media(max-width:640px){.profile-activity-head{gap:10px;font-size:13px;}.profile-activity-shell{max-width:100%;}}
```

- [ ] **Step 4: Add the fourth view control and Profile container**

Make the following structural changes:

```html
<!-- Replace the first Stats summary section's opening tag with: -->
<section id="statsSummaryCards" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">

<!-- Replace the second Stats insight section's opening tag with: -->
<section id="statsInsightCards" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">

<!-- Give the existing heading an ID so Profile can rename it without hard-coded text. -->
<h2 id="statsViewTitle" class="text-base font-extrabold mono" data-i18n="dailyActivity">Daily Activity</h2>

<!-- Append Profile to the existing Month / Year / 3D controls. -->
<button id="viewProfile" class="btn btn-ghost" type="button" data-i18n="profileView">Profile</button>

<!-- Add an ID to the existing Metric control wrapper. -->
<div id="statsMetricControls" class="flex items-center gap-2 rounded-xl border px-2 py-1.5" style="border-color: var(--color-border); background: rgba(255,255,255,0.42);">

<!-- Insert immediately before calendarMonthView. -->
<div id="calendarProfileView" style="display:none;">
  <div class="profile-activity-shell">
    <div class="profile-activity-summary-scroll">
      <dl class="profile-activity-summary">
        <div class="profile-activity-stat"><dd id="profileStatRecordedTokens">—</dd><dt data-i18n="recordedTokens">Recorded tokens</dt></div>
        <div class="profile-activity-stat"><dd id="profileStatPeakDay">—</dd><dt data-i18n="profilePeakTokens">Peak tokens</dt></div>
        <div class="profile-activity-stat"><dd id="profileStatActiveDays">—</dd><dt data-i18n="activeDays">Active Days</dt></div>
        <div class="profile-activity-stat"><dd id="profileStatCurrentStreak">—</dd><dt data-i18n="streak">Streak</dt></div>
        <div class="profile-activity-stat"><dd id="profileStatLongestStreak">—</dd><dt data-i18n="longestStreak">Longest Streak</dt></div>
      </dl>
    </div>
    <div class="profile-activity-head">
      <h3 data-i18n="tokenActivity">Token activity</h3>
      <button id="profileModeDaily" class="profile-activity-mode" type="button" aria-pressed="true" data-i18n="daily">Daily</button>
      <button id="profileModeWeekly" class="profile-activity-mode" type="button" aria-pressed="false" data-i18n="weekly">Weekly</button>
      <button id="profileModeCumulative" class="profile-activity-mode" type="button" aria-pressed="false" data-i18n="cumulative">Cumulative</button>
    </div>
    <div id="profileActivityScroller" class="profile-activity-scroll">
      <div class="profile-activity-grid-wrap">
        <div id="profileActivityGrid" class="profile-activity-grid" role="grid" aria-label="Token activity"></div>
        <div id="profileActivityWeekHits" class="profile-activity-week-hits" hidden></div>
      </div>
      <div id="profileActivityMonths" class="profile-activity-months" aria-hidden="true"></div>
    </div>
    <div id="profileActivityTooltip" class="profile-activity-tooltip" role="tooltip" hidden></div>
  </div>
</div>
```

- [ ] **Step 5: Add both language dictionaries' strings**

Add these exact entries once under `I18N.en` and once under `I18N.zh`:

```javascript
// English
profileView: 'Profile',
recordedTokens: 'Recorded tokens',
profilePeakTokens: 'Peak tokens',
tokenActivity: 'Token activity',
daily: 'Daily',
weekly: 'Weekly',
cumulative: 'Cumulative',
estimatedCost: 'Estimated cost',

// Simplified Chinese
profileView: '活动概览',
recordedTokens: '已记录 Token',
profilePeakTokens: '峰值 Token',
tokenActivity: 'Token 活跃度',
daily: '每日',
weekly: '每周',
cumulative: '累计',
estimatedCost: '预估费用',
```

- [ ] **Step 6: Run the contract test and all focused tests**

```bash
uv run --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest tests/test_profile_stats_frontend.py -q
```

Expected: `6 passed`.

- [ ] **Step 7: Commit the Profile shell**

```bash
git add src/tokdash/static/index.html tests/test_profile_stats_frontend.py
git commit -m "feat: add profile stats view shell"
```

---

### Task 3: Rendering, tooltips, and Stats view integration

**Files:**
- Modify: `src/tokdash/static/index.html:5750-6105, 7030-7040`
- Modify: `tests/test_profile_stats_frontend.py`

**Interfaces:**
- Consumes all pure helpers from Task 1 and DOM IDs from Task 2.
- Produces `setProfileActivityMode(mode)`, `renderProfileView()`, and Profile support in `setStatsStatus`/`setView`.

- [ ] **Step 1: Add failing integration-contract assertions**

Append these assertions to `test_profile_view_html_and_localization_contract`:

```python
    assert "function renderProfileView() {" in source
    assert "function setProfileActivityMode(mode) {" in source
    assert "function showProfileActivityTooltip(target, content) {" in source
    assert "setView('profile')" in source
    assert "renderProfileView();" in source
    assert "'calendarProfileView'" in source
```

Also add a whole-script syntax test so verification covers the shipped application script, not only individually extracted helpers:

```python
@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_main_inline_script_parses_with_node(tmp_path: Path):
    source = INDEX_HTML.read_text(encoding="utf-8")
    inline_scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", source, flags=re.DOTALL)
    main_script = max(inline_scripts, key=len)
    harness = tmp_path / "tokdash-main.js"
    harness.write_text(main_script, encoding="utf-8")
    subprocess.run(["node", "--check", str(harness)], check=True, capture_output=True, text=True)
```

- [ ] **Step 2: Run the contract test and verify the renderer is missing**

Run the single contract test command from Task 2, Step 2.

Expected: FAIL on `function renderProfileView() {`.

- [ ] **Step 3: Add Profile formatting and rendering functions**

Add below the pure functions from Task 1:

```javascript
let profileActivityMode = 'daily';
let profileActivityDidInitialScroll = false;

function getProfileActivityColor(level) {
  const safeLevel = Math.max(0, Math.min(4, Number(level) || 0));
  const index = Math.round((safeLevel / 4) * Math.max(0, HEAT_COLORS.length - 1));
  return HEAT_COLORS[index] || 'var(--color-border)';
}

function formatProfileMetricNumber(value) {
  return new Intl.NumberFormat(currentLang === 'zh' ? 'zh-CN' : 'en-US', {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(safeProfileNumber(value));
}

function formatProfileAggregateTooltip(aggregate, cumulative = false) {
  const range = aggregate?.startDate && aggregate?.endDate
    ? `${formatShortDate(aggregate.startDate, true)} → ${formatShortDate(aggregate.endDate, true)}`
    : '—';
  const singleDate = aggregate?.startDate === aggregate?.endDate;
  const heading = cumulative
    ? `${t('cumulative')} · ${range}`
    : (singleDate ? formatShortDate(aggregate.startDate, true) : range);
  const breakdown = aggregate?.tokenBreakdown || {};
  return [
    heading,
    `${t('total')}: ${formatNumber(aggregate?.totals?.tokens || 0)} ${t('tokensUnit')}`,
    `${t('input')}: ${formatNumber(breakdown.input || 0)}`,
    `${t('output')}: ${formatNumber(breakdown.output || 0)}`,
    `${t('cacheRead')}: ${formatNumber(breakdown.cacheRead || 0)}`,
    `${t('cacheWrite')}: ${formatNumber(breakdown.cacheWrite || 0)}`,
    breakdown.reasoning ? `${t('reasoning')}: ${formatNumber(breakdown.reasoning)}` : null,
    `${t('estimatedCost')}: ${formatCurrency(aggregate?.totals?.cost || 0)}`,
  ].filter(Boolean).join('\n');
}

function formatProfileDayTooltip(day) {
  return formatProfileAggregateTooltip({
    startDate: day.date,
    endDate: day.date,
    totals: day.totals || {},
    tokenBreakdown: day.tokenBreakdown || {},
  });
}

function showProfileActivityTooltip(target, content) {
  const tooltip = document.getElementById('profileActivityTooltip');
  if (!tooltip || !target || !content) return;
  tooltip.textContent = content;
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
  const tooltip = document.getElementById('profileActivityTooltip');
  if (tooltip) tooltip.hidden = true;
  if (target) target.removeAttribute('aria-describedby');
}

function bindProfileActivityTooltip(target, content) {
  target.setAttribute('aria-label', content.replaceAll('\n', ', '));
  target.addEventListener('mouseenter', () => showProfileActivityTooltip(target, content));
  target.addEventListener('mouseleave', () => hideProfileActivityTooltip(target));
  target.addEventListener('focus', () => showProfileActivityTooltip(target, content));
  target.addEventListener('blur', () => hideProfileActivityTooltip(target));
}

function renderProfileSummary(summary) {
  document.getElementById('profileStatRecordedTokens').textContent = formatProfileMetricNumber(summary.recordedTokens || 0);
  const peakValue = summary.peakDay ? profileDayTokens(summary.peakDay) : 0;
  const peak = document.getElementById('profileStatPeakDay');
  peak.textContent = formatProfileMetricNumber(peakValue);
  peak.title = summary.peakDay ? formatShortDate(summary.peakDay.date, true) : '';
  document.getElementById('profileStatActiveDays').textContent = formatNumber(summary.activeDays || 0);
  document.getElementById('profileStatCurrentStreak').textContent = pluralDays(summary.currentStreak || 0);
  document.getElementById('profileStatLongestStreak').textContent = pluralDays(summary.longestStreak || 0);
}

function renderProfileMonths(today = new Date()) {
  const labels = [];
  for (let offset = 11; offset >= 0; offset -= 1) {
    labels.push(new Date(today.getFullYear(), today.getMonth() - offset, 1)
      .toLocaleString(currentLang === 'zh' ? 'zh-CN' : 'en-US', { month: 'short' }));
  }
  document.getElementById('profileActivityMonths').replaceChildren(
    ...labels.map((label) => Object.assign(document.createElement('span'), { textContent: label }))
  );
}

function setProfileColumnHover(weekIndex, active) {
  document.querySelectorAll(`#profileActivityGrid [data-week-index="${weekIndex}"]`).forEach((cell) => {
    cell.classList.toggle('is-column-hover', active);
  });
}

function ensureProfileActivityInitialScroll() {
  if (profileActivityDidInitialScroll) return;
  const scroller = document.getElementById('profileActivityScroller');
  if (scroller && scroller.scrollWidth > scroller.clientWidth) {
    scroller.scrollLeft = scroller.scrollWidth;
    profileActivityDidInitialScroll = true;
  }
}

function renderProfileView() {
  const today = new Date();
  const days = getProfileActivityWindow(statsCache.default || calendarState.contributions || [], today);
  const weeks = groupProfileActivityWeeks(days);
  const { cells, series } = buildProfileActivityCells(profileActivityMode, days, weeks);
  const grid = document.getElementById('profileActivityGrid');
  const hits = document.getElementById('profileActivityWeekHits');
  hideProfileActivityTooltip();
  grid.replaceChildren();
  hits.replaceChildren();
  grid.style.setProperty('--profile-activity-empty', getProfileActivityColor(0));
  grid.style.setProperty('--profile-activity-strong', getProfileActivityColor(4));
  renderProfileSummary(summarizeProfileActivity(days));
  renderProfileMonths(today);

  cells.forEach((definition) => {
    const cell = document.createElement(profileActivityMode === 'daily' ? 'button' : 'span');
    cell.className = 'profile-activity-cell';
    cell.setAttribute('role', 'gridcell');
    if (profileActivityMode === 'daily') {
      cell.type = 'button';
      cell.style.background = getProfileActivityColor(definition.level);
      if (definition.day.isFuture) {
        cell.disabled = true;
        cell.setAttribute('aria-hidden', 'true');
      } else {
        const tooltip = formatProfileDayTooltip(definition.day);
        bindProfileActivityTooltip(cell, tooltip);
      }
    } else {
      cell.dataset.weekIndex = String(definition.weekIndex);
      cell.classList.toggle('is-aggregate', definition.active);
    }
    grid.appendChild(cell);
  });

  hits.hidden = profileActivityMode === 'daily';
  if (profileActivityMode !== 'daily') {
    series.forEach((aggregate, weekIndex) => {
      const hit = document.createElement('button');
      const tooltip = formatProfileAggregateTooltip(aggregate, profileActivityMode === 'cumulative');
      hit.type = 'button';
      hit.className = 'profile-activity-week-hit';
      bindProfileActivityTooltip(hit, tooltip);
      hit.addEventListener('mouseenter', () => setProfileColumnHover(weekIndex, true));
      hit.addEventListener('mouseleave', () => setProfileColumnHover(weekIndex, false));
      hit.addEventListener('focus', () => setProfileColumnHover(weekIndex, true));
      hit.addEventListener('blur', () => setProfileColumnHover(weekIndex, false));
      hits.appendChild(hit);
    });
  }

  ['daily', 'weekly', 'cumulative'].forEach((mode) => {
    const id = `profileMode${mode[0].toUpperCase()}${mode.slice(1)}`;
    document.getElementById(id).setAttribute('aria-pressed', String(profileActivityMode === mode));
  });

  requestAnimationFrame(ensureProfileActivityInitialScroll);
}

function setProfileActivityMode(mode) {
  if (!['daily', 'weekly', 'cumulative'].includes(mode)) return;
  profileActivityMode = mode;
  if (calendarState.view === 'profile' && statsLoaded) renderProfileView();
}
```

Also add the missing `cacheWrite` localization key to both dictionaries if it is not already present:

```javascript
// English
cacheWrite: 'Cache write',

// Simplified Chinese
cacheWrite: '缓存写入',
```

- [ ] **Step 4: Extend loading and sub-view switching without changing defaults**

Update `setStatsStatus`'s container list:

```javascript
['calendarProfileView', 'calendarMonthView', 'calendarYearView', 'calendar3DView'].forEach((id) => {
```

Extend `setView(view)` with the Profile button/container and duplicate-summary handling:

```javascript
function setView(view) {
  if (!['profile', 'month', 'year', '3d'].includes(view)) return;
  calendarState.view = view;

  document.getElementById('viewProfile').className = view === 'profile' ? 'btn btn-primary' : 'btn btn-ghost';
  document.getElementById('viewMonth').className = view === 'month' ? 'btn btn-primary' : 'btn btn-ghost';
  document.getElementById('viewYear').className = view === 'year' ? 'btn btn-primary' : 'btn btn-ghost';
  document.getElementById('view3D').className = view === '3d' ? 'btn btn-primary' : 'btn btn-ghost';
  const statsViewTitle = document.getElementById('statsViewTitle');
  statsViewTitle.dataset.i18n = view === 'profile' ? 'profileView' : 'dailyActivity';
  statsViewTitle.textContent = t(statsViewTitle.dataset.i18n);
  if (view !== 'profile') hideProfileActivityTooltip();
  document.getElementById('statsMetricControls').style.display = view === 'profile' ? 'none' : '';
  document.getElementById('statsSummaryCards').style.display = view === 'profile' ? 'none' : '';
  document.getElementById('statsInsightCards').style.display = view === 'profile' ? 'none' : '';
  document.getElementById('dayDetails').style.display = view === 'profile' ? 'none' : '';
  updateMetricControls();

  if (!statsLoaded) return;

  document.getElementById('calendarProfileView').style.display = view === 'profile' ? 'block' : 'none';
  document.getElementById('calendarMonthView').style.display = view === 'month' ? 'block' : 'none';
  document.getElementById('calendarYearView').style.display = view === 'year' ? 'block' : 'none';
  document.getElementById('calendar3DView').style.display = view === '3d' ? 'block' : 'none';

  if (view === 'profile') {
    renderProfileView();
  } else if (view === 'month') {
    renderMonthHeatmap();
  } else if (view === 'year') {
    const year = calendarState.yearCursor.getFullYear();
    renderYearHeatmap();
    updateTopStatsForYear();
    ensureYearStatsLoaded(year).then(() => {
      if (calendarState.view !== 'year' || calendarState.yearCursor.getFullYear() !== year) return;
      renderYearHeatmap();
      updateTopStatsForYear();
    });
  } else if (view === '3d') {
    render3DCalendar(getVisibleCalendarData('3d'));
    updateTopStatsForAllTime();
  }
}
```

Keep `calendarState.view: 'month'` unchanged.

Extend `rerenderPresentation()`'s cached Stats branch so a selected Profile view also refreshes its localized labels and `HEAT_COLORS` after a theme or language change:

```javascript
else if (calendarState.view === 'profile') renderProfileView();
else if (calendarState.view === 'month') renderMonthHeatmap();
```

Place the new Profile branch before the existing Month/Year/3D branches; do not add a fetch to `setProfileActivityMode`.

- [ ] **Step 5: Wire semantic button interactions**

Add alongside the existing heatmap control listeners:

```javascript
document.getElementById('viewProfile').addEventListener('click', () => setView('profile'));
document.getElementById('profileModeDaily').addEventListener('click', () => setProfileActivityMode('daily'));
document.getElementById('profileModeWeekly').addEventListener('click', () => setProfileActivityMode('weekly'));
document.getElementById('profileModeCumulative').addEventListener('click', () => setProfileActivityMode('cumulative'));
window.addEventListener('resize', ensureProfileActivityInitialScroll, { passive: true });
```

- [ ] **Step 6: Run focused tests**

```bash
uv run --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest tests/test_profile_stats_frontend.py -q
```

Expected: `7 passed`.

- [ ] **Step 7: Commit the complete interactive view**

```bash
git add src/tokdash/static/index.html tests/test_profile_stats_frontend.py
git commit -m "feat: render profile token activity views"
```

---

### Task 4: Local integration, regression checks, and user preview

**Files:**
- Modify only if verification exposes a defect: `src/tokdash/static/index.html`, `tests/test_profile_stats_frontend.py`

**Interfaces:**
- Consumes the complete Profile view from Tasks 1-3.
- Produces a locally running build ready for user acceptance; no remote branch, issue comment, or pull request is created in this task.

- [ ] **Step 1: Run whole-script frontend syntax and focused tests**

Run the test file containing both `test_main_inline_script_parses_with_node` (`node --check` on the complete shipped application script) and the extracted pure-helper behavior cases:

```bash
uv run --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest tests/test_profile_stats_frontend.py -q
```

Expected: all seven Profile frontend tests pass. Both the whole-script `node --check` subprocess and the extracted-helper Node subprocesses exit zero.

- [ ] **Step 2: Run the repository's CI compile command**

```bash
uv run --with-editable . --with-requirements requirements-dev.txt \
  python -m compileall -q src/tokdash main.py docs/guides/agents/openclaw_reporting/openclaw_cron_job.py
```

Expected: exit code 0 and no output.

- [ ] **Step 3: Run the full test suite**

```bash
uv run --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest -q
```

Expected: all tests pass; environment-gated tests may report skips consistent with the current suite.

- [ ] **Step 4: Record the type-check and lint status**

Run:

```bash
for command in ruff mypy pyright; do command -v "$command" || true; done
```

Expected in the current repository: no configured linter or static type checker is found. Report this explicitly rather than claiming a type check ran. The CI-equivalent compile check and Node-backed frontend tests are the applicable syntax checks.

- [ ] **Step 5: Start the feature branch locally without replacing the installed Tokdash**

```bash
uv run --with-editable . --with-requirements requirements-dev.txt \
  tokdash serve --bind 127.0.0.1 --port 55424 --no-open
```

Expected: Uvicorn listens on `http://127.0.0.1:55424` using the working-tree source. Keep this process running for user review.

- [ ] **Step 6: Perform the manual acceptance matrix**

Open `http://127.0.0.1:55424` and verify:

1. Stats still opens to Month.
2. Profile hides the duplicate existing summary/insight cards and metric selector.
3. The five Profile metrics match the visible 52-week data.
4. Daily uses square 2 px-corner cells and four theme-derived levels.
5. Weekly fills Monday-to-Sunday columns from the bottom and shows one tooltip per week.
6. Cumulative heights never decrease and the final active column fills all seven rows when recorded tokens are non-zero.
7. Daily and aggregate tooltips show available breakdown fields and estimated cost.
8. Light and dark themes recolor the view without a reload error.
9. At mobile width, the grid scrolls horizontally and initially shows the latest weeks.
10. Returning to Month, Year, and 3D preserves their previous cursors and rendering.
11. Keyboard focus opens the same tooltip content as pointer hover.
12. The browser console has no new errors.

- [ ] **Step 7: Fix only verified defects, rerun checks, and commit the fixes**

If Step 6 finds a defect, first add a focused regression assertion to `tests/test_profile_stats_frontend.py`, verify it fails, make the smallest correction, and rerun Steps 1-3. Commit only after checks pass:

```bash
git add src/tokdash/static/index.html tests/test_profile_stats_frontend.py
git commit -m "fix: polish profile stats interactions"
```

If Step 6 finds no defect, do not create an empty commit.

- [ ] **Step 8: Hand the local URL to the user and stop before external publication**

Report the local URL, completed checks, compatibility impact, and any unavailable type/lint target. Wait for explicit user approval before pushing the branch, commenting on Issue #10, or opening a pull request.
