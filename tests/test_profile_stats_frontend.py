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
    "function buildOverviewProfilePreview(contributions, today = new Date()) {",
]


def _run_profile_js(tmp_path: Path, expression: str, payload: dict) -> object:
    source = INDEX_HTML.read_text(encoding="utf-8")
    functions = "\n".join(
        _extract_js_function(source, signature) for signature in PROFILE_FUNCTIONS
    )
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


TOOLTIP_JS_SETUP = """
const LABELS = {
  cumulative: 'Cumulative', total: 'Total', tokensUnit: 'tokens',
  input: 'Input', output: 'Output', cacheRead: 'Cache read',
  cacheWrite: 'Cache write', reasoning: 'Reasoning',
  estimatedCost: 'Estimated cost',
};
function t(key) { return LABELS[key] || key; }
function formatNumber(value) { return new Intl.NumberFormat('en-US').format(Number(value) || 0); }
function formatCurrency(value) { return `$${(Number(value) || 0).toFixed(2)}`; }
function formatShortDate(value) { return value || '—'; }
"""


def _run_profile_tooltip_js(tmp_path: Path, expression: str, payload: dict) -> object:
    source = INDEX_HTML.read_text(encoding="utf-8")
    functions = "\n".join(
        [
            _extract_js_function(source, "function safeProfileNumber(value) {"),
            _extract_js_function(
                source,
                "function formatProfileAggregateTooltip(aggregate, cumulative = false) {",
            ),
        ]
    )
    harness = tmp_path / "profile-tooltip.js"
    harness.write_text(
        TOOLTIP_JS_SETUP
        + "\n"
        + functions
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
    assert next(day for day in result if day["date"] == "2026-01-06")["totals"][
        "tokens"
    ] == 20


@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_profile_summary_excludes_future_and_calculates_streaks(tmp_path: Path):
    payload = {
        "today": "2026-01-07",
        "days": [
            _day("2025-12-29", 4),
            _day("2025-12-30", 4),
            _day("2025-12-31", 4),
            _day("2026-01-01", 4),
            _day("2026-01-02", 4),
            _day("2026-01-05", 10),
            _day("2026-01-06", 20),
            _day("2026-01-07", 30),
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
        sum(
            cell["active"]
            for cell in result["weekly"]["cells"][offset : offset + 7]
        )
        for offset in (0, 7)
    ]
    cumulative_heights = [
        sum(
            cell["active"]
            for cell in result["cumulative"]["cells"][offset : offset + 7]
        )
        for offset in (0, 7)
    ]
    assert weekly_heights == [3, 7]
    assert cumulative_heights == [2, 7]
    assert cumulative_heights == sorted(cumulative_heights)
    assert result["cumulative"]["series"][1]["startDate"] == "2025-12-29"
    assert result["cumulative"]["series"][1]["endDate"] == "2026-01-11"
    assert result["levels"] == [0, 1, 1, 2, 3, 4]


@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_profile_default_window_is_52_weeks_and_empty_or_zero_data_is_safe(
    tmp_path: Path,
):
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
    today_cell = next(
        cell for cell in result["cells"] if cell["day"]["date"] == payload["today"]
    )
    assert today_cell["level"] == 4
    assert result["cells"][-1]["day"]["isFuture"] is True
    assert result["cells"][-1]["level"] == 0


@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_profile_week_aggregates_breakdown_and_cost_across_year_boundary(
    tmp_path: Path,
):
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


@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_profile_tooltip_model_has_semantic_rows_and_accessible_text(tmp_path: Path):
    payload = {
        "aggregate": {
            "startDate": "2026-07-20",
            "endDate": "2026-07-26",
            "totals": {"tokens": 1234, "cost": 1.25},
            "tokenBreakdown": {
                "input": 500,
                "output": 300,
                "cacheRead": 250,
                "cacheWrite": 100,
                "reasoning": 84,
            },
        }
    }
    result = _run_profile_tooltip_js(
        tmp_path,
        "formatProfileAggregateTooltip(payload.aggregate)",
        payload,
    )
    assert result["title"] == "2026-07-20 → 2026-07-26"
    assert [row["key"] for row in result["rows"]] == [
        "total",
        "input",
        "output",
        "cacheRead",
        "cacheWrite",
        "reasoning",
        "estimatedCost",
    ]
    assert [row["tone"] for row in result["rows"]] == [
        "primary",
        "primary",
        "secondary",
        "cost",
        "cta",
        "reasoning",
        "cost",
    ]
    assert result["rows"][0] == {
        "key": "total",
        "label": "Total",
        "value": "1,234 tokens",
        "tone": "primary",
        "prominent": True,
    }
    assert result["accessibleText"] == (
        "2026-07-20 → 2026-07-26. Total: 1,234 tokens. Input: 500. "
        "Output: 300. Cache read: 250. Cache write: 100. Reasoning: 84. "
        "Estimated cost: $1.25"
    )


@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_profile_tooltip_keeps_zero_rows_and_omits_zero_reasoning(tmp_path: Path):
    payload = {
        "aggregate": {
            "startDate": "2026-07-20",
            "endDate": "2026-07-26",
            "totals": {"tokens": 0, "cost": 0},
            "tokenBreakdown": {
                "input": 0,
                "output": 0,
                "cacheRead": 0,
                "cacheWrite": 0,
                "reasoning": 0,
            },
        }
    }
    result = _run_profile_tooltip_js(
        tmp_path,
        "formatProfileAggregateTooltip(payload.aggregate, true)",
        payload,
    )
    assert result["title"] == "Cumulative · 2026-07-20 → 2026-07-26"
    assert [row["key"] for row in result["rows"]] == [
        "total",
        "input",
        "output",
        "cacheRead",
        "cacheWrite",
        "estimatedCost",
    ]
    assert [row["value"] for row in result["rows"]] == [
        "0 tokens",
        "0",
        "0",
        "0",
        "0",
        "$0.00",
    ]
    assert "Reasoning" not in result["accessibleText"]


def test_profile_view_html_and_localization_contract():
    source = INDEX_HTML.read_text(encoding="utf-8")
    required_ids = [
        "statsViewTitle",
        "viewProfile",
        "statsMetricControls",
        "calendarProfileView",
        "profileStatRecordedTokens",
        "profileStatPeakDay",
        "profileStatActiveDays",
        "profileStatCurrentStreak",
        "profileStatLongestStreak",
        "profileActivityGrid",
        "profileActivityWeekHits",
        "profileActivityMonths",
        "profileActivityScroller",
        "profileActivityTooltip",
        "profileModeDaily",
        "profileModeWeekly",
        "profileModeCumulative",
    ]
    for element_id in required_ids:
        assert f'id="{element_id}"' in source
    assert source.count("profileView: '") == 2
    assert source.count("recordedTokens: '") == 2
    assert source.count("tokenActivity: '") == 2
    assert ".profile-activity-cell" in source
    assert "border-radius:2px" in source.replace(" ", "")
    assert "function renderProfileView() {" in source
    assert "function setProfileActivityMode(mode) {" in source
    assert "function showProfileActivityTooltip(target, model) {" in source
    assert "setView('profile')" in source
    assert "renderProfileView();" in source
    assert "'calendarProfileView'" in source


def test_profile_visual_polish_contract():
    source = INDEX_HTML.read_text(encoding="utf-8")
    compact = re.sub(r"\s+", "", source)
    assert re.findall(
        r'class="profile-activity-stat" data-tone="([^"]+)"', source
    ) == ["primary", "secondary", "cost", "cta", "primary"]
    assert '.profile-activity-head h3::before' in source
    assert '.profile-activity-mode[aria-pressed="true"]' in source
    assert '.profile-activity-tooltip-header' in source
    assert '.profile-activity-tooltip-row[data-tone="reasoning"]' in source
    assert '.profile-activity-tooltip-row[data-key="estimatedCost"]' in source
    assert "button.profile-activity-cell:not(:disabled):is(:hover,:focus-visible)" in source
    assert ".profile-activity-cell{transform:none!important;}" in compact

    renderer = _extract_js_function(
        source,
        "function renderProfileActivityTooltipContent(tooltip, model) {",
    )
    assert "document.createElement(" in renderer
    assert ".textContent =" in renderer
    assert "tooltip.replaceChildren(header, body);" in renderer
    assert ".innerHTML" not in renderer

    binder = _extract_js_function(
        source,
        "function bindProfileActivityTooltip(target, model) {",
    )
    assert "model.accessibleText" in binder
    assert "content.replaceAll" not in binder

    resolver = _extract_js_function(
        source, "function resolveProfileActivityTooltip(target) {"
    )
    assert "dataset.profileTooltipId" in resolver
    assert "profileActivityTooltip" in resolver


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
    assert "shell?.dataset.state !== 'error'" in renderer
    assert "target?.dataset.profileTooltipId || 'profileActivityTooltip'" in resolver
    assert "renderOverviewProfilePreview();" in _extract_js_function(
        source, "function renderOverviewTab(data) {"
    )


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


@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_main_inline_script_parses_with_node(tmp_path: Path):
    source = INDEX_HTML.read_text(encoding="utf-8")
    inline_scripts = re.findall(
        r"<script(?:\s[^>]*)?>(.*?)</script>", source, flags=re.DOTALL
    )
    main_script = max(inline_scripts, key=len)
    harness = tmp_path / "tokdash-main.js"
    harness.write_text(main_script, encoding="utf-8")
    subprocess.run(
        ["node", "--check", str(harness)],
        check=True,
        capture_output=True,
        text=True,
    )
