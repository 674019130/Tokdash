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
