# Profile Visual Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add medium-strength, theme-native visual emphasis to Profile statistics, activity controls, heatmap interactions, and tooltips without changing any Profile calculations or calendar geometry.

**Architecture:** Keep the work frontend-only in the existing embedded `index.html`. First convert tooltip formatting into a pure structured model and render it through safe DOM construction, then layer namespaced semantic tone hooks and theme-derived CSS onto the existing markup and interactions. Extend the existing Node-backed pytest file so data presentation, safe rendering contracts, accessibility text, and shipped-script syntax remain independently verifiable.

**Tech Stack:** HTML/CSS, browser JavaScript embedded in `src/tokdash/static/index.html`, Python 3.10+ pytest harnesses, Node.js for extracted JavaScript and whole-script syntax checks, existing CSS theme variables and `color-mix()` support.

## Global Constraints

- Do not change Profile statistics, aggregation, date windows, heatmap levels, API requests, persistence, or backend code.
- Preserve exactly 52 Monday-to-Sunday columns, seven square cells per column, 3 px gaps, 2 px corners, and the 732 CSS px desktop width cap.
- Preserve the current resting heatmap palette; emphasis applies only to summary values, controls, active hover/focus targets, and tooltip presentation.
- Use only existing theme variables such as `--color-primary`, `--color-secondary`, `--color-cost`, `--color-cta`, `--color-border`, `--color-muted`, and `--color-surface-glass`; do not add light-only or dark-only hard-coded colors.
- Keep Input, Output, Cache read, Cache write, and Estimated cost visible when their values are zero. Omit Reasoning only when its value is zero.
- Use `document.createElement()`, `textContent`, and `replaceChildren()` for tooltip content; do not interpolate tooltip values through `innerHTML`.
- Preserve pointer-hover and keyboard-focus parity, complete target `aria-label` text, `role="tooltip"`, and `aria-pressed` on activity-mode buttons.
- Preserve Month, Year, 3D, language switching, theme switching, responsive scrolling, and cursor state.
- Never delete files. Do not add `.superpowers/` visual-companion artifacts to Git.
- The Last Week quick-range preset, share cards, profile identity, new data fields, and new dependencies remain out of scope.
- Before handoff, run focused tests, the repository's CI compile check, the full pytest suite, the whole-script Node syntax check, and the available type/lint discovery. Report pre-existing failures exactly.

---

## File Map

- Modify: `src/tokdash/static/index.html`
  - Owns Profile semantic markup hooks, theme-derived CSS, tooltip model formatting, safe DOM rendering, positioning, and interaction binding.
- Modify: `tests/test_profile_stats_frontend.py`
  - Adds extracted tooltip-model behavior tests and static contracts for semantic tone hooks, safe DOM construction, accessibility binding, and visual selectors.
- Reference only: `docs/superpowers/specs/2026-07-27-profile-visual-polish-design.md`
  - Approved visual treatment, compatibility requirements, and pull-request boundary.
- Reference only: `docs/superpowers/specs/2026-07-27-profile-stats-view-design.md`
  - Existing Profile calculation, geometry, accessibility, and navigation behavior that must remain unchanged.

---

### Task 1: Structured tooltip presentation model

**Files:**
- Modify: `src/tokdash/static/index.html:6055-6083`
- Modify: `tests/test_profile_stats_frontend.py:47-67, 232-269`

**Interfaces:**
- Consumes: existing `safeProfileNumber(value)`, `formatShortDate(value, includeYear)`, `formatNumber(value)`, `formatCurrency(value)`, and `t(key)` helpers.
- Produces:
  - `formatProfileAggregateTooltip(aggregate, cumulative = false) -> {title: string, rows: ProfileTooltipRow[], accessibleText: string}`
  - `ProfileTooltipRow -> {key: string, label: string, value: string, tone: 'primary'|'secondary'|'cost'|'cta'|'reasoning', prominent: boolean}`
  - `formatProfileDayTooltip(day) -> {title, rows, accessibleText}` through the same aggregate formatter.

- [ ] **Step 1: Add a Node harness for the extracted tooltip formatter**

Add below `_run_profile_js` in `tests/test_profile_stats_frontend.py`:

```python
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
```

- [ ] **Step 2: Write failing tests for row order, tones, accessible text, and zero-value retention**

Insert before `test_profile_view_html_and_localization_contract`:

```python
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
```

- [ ] **Step 3: Run the two new tests and verify the current string formatter fails**

Run:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest \
  tests/test_profile_stats_frontend.py::test_profile_tooltip_model_has_semantic_rows_and_accessible_text \
  tests/test_profile_stats_frontend.py::test_profile_tooltip_keeps_zero_rows_and_omits_zero_reasoning -q
```

Expected: both tests fail because `formatProfileAggregateTooltip` currently returns a string rather than an object with `title`, `rows`, and `accessibleText`.

- [ ] **Step 4: Replace the plain tooltip formatter with the structured model**

Replace `formatProfileAggregateTooltip` in `src/tokdash/static/index.html` with:

```javascript
function formatProfileAggregateTooltip(aggregate, cumulative = false) {
  const range = aggregate?.startDate && aggregate?.endDate
    ? `${formatShortDate(aggregate.startDate, true)} → ${formatShortDate(aggregate.endDate, true)}`
    : '—';
  const singleDate = aggregate?.startDate === aggregate?.endDate;
  const title = cumulative
    ? `${t('cumulative')} · ${range}`
    : (singleDate ? formatShortDate(aggregate.startDate, true) : range);
  const breakdown = aggregate?.tokenBreakdown || {};
  const definitions = [
    {
      key: 'total',
      label: t('total'),
      value: `${formatNumber(safeProfileNumber(aggregate?.totals?.tokens))} ${t('tokensUnit')}`,
      tone: 'primary',
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
  const accessibleText = [title, ...rows.map((row) => `${row.label}: ${row.value}`)].join('. ');
  return { title, rows, accessibleText };
}
```

Keep `formatProfileDayTooltip(day)` unchanged; it now returns the structured object from this function.

- [ ] **Step 5: Run all focused Profile tests**

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest tests/test_profile_stats_frontend.py -q
```

Expected: the two new model tests pass; the existing seven tests also pass, for `9 passed` total.

- [ ] **Step 6: Commit the independently tested tooltip model**

```bash
git add src/tokdash/static/index.html tests/test_profile_stats_frontend.py
git commit -m "feat: structure profile tooltip content"
```

---

### Task 2: Safe tooltip DOM and semantic visual emphasis

**Files:**
- Modify: `src/tokdash/static/index.html:447-471, 851-853, 1527-1548, 6085-6115`
- Modify: `tests/test_profile_stats_frontend.py:234-269`

**Interfaces:**
- Consumes: the `{title, rows, accessibleText}` tooltip model from Task 1 and existing theme variables.
- Produces:
  - `renderProfileActivityTooltipContent(tooltip: HTMLElement, model: ProfileTooltipModel) -> void`
  - `showProfileActivityTooltip(target: HTMLElement, model: ProfileTooltipModel) -> void`
  - `bindProfileActivityTooltip(target: HTMLElement, model: ProfileTooltipModel) -> void`
  - summary `data-tone` hooks and namespaced Profile CSS states.

- [ ] **Step 1: Add a failing contract test for semantic hooks and safe rendering**

In the existing `test_profile_view_html_and_localization_contract`, replace the old formatter-argument assertion with the new model signature:

```python
    assert "function showProfileActivityTooltip(target, model) {" in source
```

Insert before `test_main_inline_script_parses_with_node`:

```python
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
```

- [ ] **Step 2: Run the contract test and verify the semantic hooks are absent**

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest tests/test_profile_stats_frontend.py::test_profile_visual_polish_contract -q
```

Expected: FAIL because the five summary elements do not yet have `data-tone` attributes and the structured tooltip renderer is absent.

- [ ] **Step 3: Add semantic tone hooks to the five summary items**

Replace the five summary item lines inside `profile-activity-summary` with:

```html
<div class="profile-activity-stat" data-tone="primary"><dd id="profileStatRecordedTokens">—</dd><dt data-i18n="recordedTokens">Recorded tokens</dt></div>
<div class="profile-activity-stat" data-tone="secondary"><dd id="profileStatPeakDay">—</dd><dt data-i18n="profilePeakTokens">Peak tokens</dt></div>
<div class="profile-activity-stat" data-tone="cost"><dd id="profileStatActiveDays">—</dd><dt data-i18n="activeDays">Active Days</dt></div>
<div class="profile-activity-stat" data-tone="cta"><dd id="profileStatCurrentStreak">—</dd><dt data-i18n="streak">Streak</dt></div>
<div class="profile-activity-stat" data-tone="primary"><dd id="profileStatLongestStreak">—</dd><dt data-i18n="longestStreak">Longest Streak</dt></div>
```

- [ ] **Step 4: Replace the Profile CSS block with theme-derived semantic styles**

Replace the existing `.profile-activity-shell` through mobile media-query block with:

```css
.profile-activity-shell{max-width:732px;margin:0 auto;}
.profile-activity-summary-scroll{overflow-x:auto;padding-bottom:2px;}
.profile-activity-summary{display:grid;grid-template-columns:repeat(5,minmax(120px,1fr));min-width:600px;border:1px solid color-mix(in srgb,var(--color-primary) 18%,var(--color-border));border-radius:16px;overflow:hidden;background:color-mix(in srgb,var(--color-surface-glass) 88%,transparent);box-shadow:inset 0 1px 0 color-mix(in srgb,var(--color-primary) 13%,transparent),0 12px 32px color-mix(in srgb,var(--color-primary) 7%,transparent);}
.profile-activity-stat{--profile-stat-tone:var(--color-primary);position:relative;padding:12px 8px;text-align:center;}
.profile-activity-stat[data-tone="secondary"]{--profile-stat-tone:var(--color-secondary);}
.profile-activity-stat[data-tone="cost"]{--profile-stat-tone:var(--color-cost);}
.profile-activity-stat[data-tone="cta"]{--profile-stat-tone:var(--color-cta);}
.profile-activity-stat+.profile-activity-stat::before{content:"";position:absolute;left:0;top:14px;bottom:14px;width:1px;background:var(--color-border);}
.profile-activity-stat dd{margin:0;color:var(--profile-stat-tone);font-weight:850;font-size:15px;text-shadow:0 0 14px color-mix(in srgb,var(--profile-stat-tone) 20%,transparent);}
.profile-activity-stat dt{margin-top:3px;color:var(--color-muted);font-size:12px;white-space:nowrap;}
.profile-activity-head{display:flex;align-items:center;gap:8px;margin:32px 0 12px;}
.profile-activity-head h3{display:flex;align-items:center;gap:8px;margin-right:auto;font-size:16px;font-weight:800;}
.profile-activity-head h3::before{content:"";width:4px;height:16px;border-radius:999px;background:var(--color-primary);box-shadow:0 0 12px color-mix(in srgb,var(--color-primary) 38%,transparent);}
.profile-activity-mode{border:1px solid transparent;border-radius:999px;padding:5px 9px;background:transparent;color:var(--color-muted);font:inherit;line-height:1.2;cursor:pointer;transition:color .15s ease,background .15s ease,border-color .15s ease,box-shadow .15s ease;}
.profile-activity-mode:is(:hover,:focus-visible){color:var(--color-text);border-color:color-mix(in srgb,var(--color-primary) 18%,transparent);background:color-mix(in srgb,var(--color-primary) 8%,transparent);}
.profile-activity-mode:focus-visible{outline:2px solid color-mix(in srgb,var(--color-primary) 52%,transparent);outline-offset:2px;}
.profile-activity-mode[aria-pressed="true"]{color:var(--color-primary);border-color:color-mix(in srgb,var(--color-primary) 32%,transparent);background:color-mix(in srgb,var(--color-primary) 13%,transparent);box-shadow:inset 0 1px 0 color-mix(in srgb,var(--color-primary) 18%,transparent),0 0 14px color-mix(in srgb,var(--color-primary) 10%,transparent);}
.profile-activity-scroll{overflow-x:auto;padding:8px 0 12px;}
.profile-activity-grid-wrap{position:relative;min-width:572px;}
.profile-activity-grid{display:grid;grid-auto-flow:column;grid-template-columns:repeat(52,minmax(8px,1fr));grid-template-rows:repeat(7,minmax(8px,1fr));gap:3px;width:100%;}
.profile-activity-cell{width:100%;aspect-ratio:1;border:0;border-radius:2px;background:var(--profile-activity-empty,var(--color-border));padding:0;position:relative;transition:filter .12s ease,transform .12s ease,box-shadow .12s ease;}
button.profile-activity-cell{cursor:pointer;}
button.profile-activity-cell:not(:disabled):is(:hover,:focus-visible){z-index:1;outline:none;filter:brightness(1.14);transform:translateY(-1px);box-shadow:0 0 0 1px color-mix(in srgb,var(--color-primary) 62%,transparent),0 4px 10px color-mix(in srgb,var(--color-primary) 20%,transparent);}
.profile-activity-cell.is-aggregate{background:var(--profile-activity-strong,var(--color-primary));}
.profile-activity-cell.is-column-hover.is-aggregate{filter:brightness(1.16);box-shadow:0 0 0 1px color-mix(in srgb,var(--profile-activity-strong,var(--color-primary)) 72%,transparent),0 0 9px color-mix(in srgb,var(--color-primary) 18%,transparent);}
.profile-activity-cell.is-column-hover:not(.is-aggregate){background:color-mix(in srgb,var(--color-primary) 16%,var(--color-border));box-shadow:0 0 0 1px color-mix(in srgb,var(--color-primary) 30%,transparent);}
.profile-activity-week-hits{position:absolute;inset:0;display:grid;grid-template-columns:repeat(52,minmax(8px,1fr));gap:3px;pointer-events:none;}
.profile-activity-week-hit{position:relative;min-width:8px;border:0;background:transparent;padding:0;pointer-events:auto;cursor:pointer;}
.profile-activity-week-hit:focus-visible{outline:2px solid color-mix(in srgb,var(--color-primary) 62%,transparent);outline-offset:2px;border-radius:2px;}
.profile-activity-tooltip{position:fixed;z-index:120;width:min(260px,calc(100vw - 16px));padding:0;overflow:hidden;border:1px solid color-mix(in srgb,var(--color-primary) 24%,var(--color-border));border-radius:10px;background:color-mix(in srgb,var(--color-surface-glass) 96%,var(--color-bg));color:var(--color-text);box-shadow:var(--shadow-md),0 0 24px color-mix(in srgb,var(--color-primary) 10%,transparent);white-space:normal;text-align:left;font-size:11px;line-height:1.35;pointer-events:none;backdrop-filter:blur(18px);}
.profile-activity-tooltip[hidden]{display:none;}
.profile-activity-tooltip-header{padding:8px 10px;border-bottom:1px solid color-mix(in srgb,var(--color-primary) 20%,var(--color-border));background:color-mix(in srgb,var(--color-primary) 12%,transparent);color:var(--color-primary);font-weight:800;letter-spacing:.01em;}
.profile-activity-tooltip-body{padding:6px 10px 8px;}
.profile-activity-tooltip-row{--profile-tooltip-tone:var(--color-primary);display:grid;grid-template-columns:6px minmax(0,1fr) auto;align-items:center;gap:7px;padding:3px 0;}
.profile-activity-tooltip-row[data-tone="secondary"]{--profile-tooltip-tone:var(--color-secondary);}
.profile-activity-tooltip-row[data-tone="cost"]{--profile-tooltip-tone:var(--color-cost);}
.profile-activity-tooltip-row[data-tone="cta"]{--profile-tooltip-tone:var(--color-cta);}
.profile-activity-tooltip-row[data-tone="reasoning"]{--profile-tooltip-tone:color-mix(in srgb,var(--color-primary) 55%,var(--color-secondary));}
.profile-activity-tooltip-row[data-prominent="true"]{margin:1px 0 4px;padding:6px;border:1px solid color-mix(in srgb,var(--profile-tooltip-tone) 18%,transparent);border-radius:7px;background:color-mix(in srgb,var(--profile-tooltip-tone) 8%,transparent);}
.profile-activity-tooltip-row[data-key="estimatedCost"]{margin-top:4px;padding-top:7px;border-top:1px solid var(--color-border);}
.profile-activity-tooltip-dot{width:6px;height:6px;border-radius:50%;background:var(--profile-tooltip-tone);box-shadow:0 0 7px color-mix(in srgb,var(--profile-tooltip-tone) 42%,transparent);}
.profile-activity-tooltip-label{min-width:0;color:var(--color-muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.profile-activity-tooltip-value{color:var(--profile-tooltip-tone);font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;font-variant-numeric:tabular-nums;font-weight:750;text-align:right;white-space:nowrap;}
.profile-activity-tooltip-row[data-prominent="true"] .profile-activity-tooltip-value{font-size:13px;font-weight:850;}
.profile-activity-months{display:flex;justify-content:space-between;min-width:572px;margin-top:8px;color:var(--color-muted);font-size:12px;}
@media(max-width:640px){.profile-activity-head{gap:6px;flex-wrap:wrap;font-size:13px;}.profile-activity-head h3{flex:1 0 100%;margin-bottom:2px;}.profile-activity-mode{padding:5px 8px;}.profile-activity-shell{max-width:100%;}}
```

Inside the existing `@media (prefers-reduced-motion: reduce)` block, add the Profile transform reset after the universal transition rule:

```css
.profile-activity-cell{transform:none!important;}
```

- [ ] **Step 5: Add the safe structured tooltip renderer and update binding**

Replace `showProfileActivityTooltip` and `bindProfileActivityTooltip` while keeping the current positioning and hide logic:

```javascript
function renderProfileActivityTooltipContent(tooltip, model) {
  const header = document.createElement('div');
  header.className = 'profile-activity-tooltip-header';
  header.textContent = model.title;

  const body = document.createElement('div');
  body.className = 'profile-activity-tooltip-body';
  model.rows.forEach((row) => {
    const item = document.createElement('div');
    item.className = 'profile-activity-tooltip-row';
    item.dataset.key = row.key;
    item.dataset.tone = row.tone;
    if (row.prominent) item.dataset.prominent = 'true';

    const dot = document.createElement('span');
    dot.className = 'profile-activity-tooltip-dot';
    dot.setAttribute('aria-hidden', 'true');
    const label = document.createElement('span');
    label.className = 'profile-activity-tooltip-label';
    label.textContent = row.label;
    const value = document.createElement('span');
    value.className = 'profile-activity-tooltip-value';
    value.textContent = row.value;
    item.append(dot, label, value);
    body.appendChild(item);
  });
  tooltip.replaceChildren(header, body);
}

function showProfileActivityTooltip(target, model) {
  const tooltip = document.getElementById('profileActivityTooltip');
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

function bindProfileActivityTooltip(target, model) {
  target.setAttribute('aria-label', model.accessibleText);
  target.addEventListener('mouseenter', () => showProfileActivityTooltip(target, model));
  target.addEventListener('mouseleave', () => hideProfileActivityTooltip(target));
  target.addEventListener('focus', () => showProfileActivityTooltip(target, model));
  target.addEventListener('blur', () => hideProfileActivityTooltip(target));
}
```

Do not change `hideProfileActivityTooltip`, the Daily/Weekly/Cumulative call sites, aggregation helpers, or tooltip positioning math.

- [ ] **Step 6: Run the contract and all focused Profile tests**

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest tests/test_profile_stats_frontend.py -q
```

Expected: `10 passed`. The existing `test_main_inline_script_parses_with_node` also confirms the complete shipped script passes `node --check`.

- [ ] **Step 7: Commit the visual and safe-rendering layer**

```bash
git add src/tokdash/static/index.html tests/test_profile_stats_frontend.py
git commit -m "feat: polish profile activity highlights"
```

---

### Task 3: Regression checks and local visual acceptance

**Files:**
- Modify only if a verified defect is found: `src/tokdash/static/index.html`, `tests/test_profile_stats_frontend.py`

**Interfaces:**
- Consumes: the structured tooltip model and semantic styling from Tasks 1-2.
- Produces: a locally running build ready for the user's visual approval; no push, issue comment, or pull request is created.

- [ ] **Step 1: Run the focused frontend suite**

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest tests/test_profile_stats_frontend.py -q
```

Expected: `10 passed`, including extracted model behavior and whole-script Node syntax.

- [ ] **Step 2: Run the repository's CI compile command**

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt \
  python -m compileall -q src/tokdash main.py docs/guides/agents/openclaw_reporting/openclaw_cron_job.py
```

Expected: exit code 0 and no output.

- [ ] **Step 3: Run the full pytest suite and compare failures with the current baseline**

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt --with pytest \
  python -m pytest -q
```

Expected feature result: all Profile tests pass. The current environment baseline is `689 passed, 3 skipped, 3 failed`; after adding the three tests in this plan, an otherwise unchanged run should report `692 passed, 3 skipped, 3 failed`. The unrelated failures are two order-sensitive doctor cases that pass with `tests/test_onboard.py` alone and one Asia/Hong_Kong calendar-month case that passes with `TZ=UTC`. Record the exact test names and diagnostics from this run, and investigate any new or changed failure before handoff.

- [ ] **Step 4: Record configured type-check and lint availability**

Run:

```bash
rg -n "\[tool\.(ruff|mypy|pyright)|ruff|mypy|pyright" pyproject.toml requirements-dev.txt .github || true
```

Expected in the current repository: no configured Python or JavaScript type-check target and no configured ruff target. Report the exact command and empty result. The CI compile command and `node --check` test are the applicable syntax checks; do not claim an unavailable type checker ran.

- [ ] **Step 5: Confirm the existing local server is serving the working tree**

```bash
curl -fsS http://127.0.0.1:55424/health
```

Expected: HTTP success from the Tokdash server already running at `http://127.0.0.1:55424/`. If the process is no longer running, start the same editable checkout with:

```bash
uv run --no-project --with-editable . --with-requirements requirements-dev.txt \
  tokdash serve --bind 127.0.0.1 --port 55424 --no-open
```

- [ ] **Step 6: Perform the manual visual and interaction matrix**

Open `http://127.0.0.1:55424/` and verify all of the following:

1. Profile summary values use the approved primary, secondary, cost, CTA, primary tone sequence in light and dark themes.
2. The summary strip has one restrained overall highlight; individual statistics do not look like five separately filled cards.
3. Daily, Weekly, and Cumulative controls keep stable positions; the active control has a tinted pill and visible focus state.
4. Daily hover/focus adds a ring, brightness, and at most a one-pixel lift without changing the 52-by-7 grid measurements.
5. Weekly and Cumulative target the correct column, strengthen filled cells, softly tint empty historical cells, and leave future cells unchanged.
6. Tooltip header, prominent Total row, colored dots, neutral labels, right-aligned tabular values, and cost separator are readable without crowding.
7. Input, Output, Cache read, Cache write, and Estimated cost remain visible at zero; Reasoning appears only when non-zero.
8. Pointer hover and keyboard focus show the same tooltip content; targets expose the complete plain-text `aria-label`.
9. English and Simplified Chinese labels fit without clipping, including on the narrow viewport.
10. At mobile width, mode controls wrap cleanly above the horizontally scrollable heatmap and the tooltip remains inside the viewport.
11. With reduced motion enabled, no heatmap cell translates while hover/focus emphasis remains visible.
12. The grid still has 364 square cells, 3 px gaps, 2 px corners, a 732 px desktop cap, and unchanged Daily/Weekly/Cumulative fill shapes.
13. Switching among Profile, Month, Year, and 3D preserves the previous view state and introduces no browser-console errors.

- [ ] **Step 7: Fix only verified defects with a regression assertion**

For each defect found in Step 6, add the smallest focused assertion to `tests/test_profile_stats_frontend.py`, run that assertion to confirm it fails, make the smallest correction in `src/tokdash/static/index.html`, and rerun Steps 1-4. Commit verified corrections with:

```bash
git add src/tokdash/static/index.html tests/test_profile_stats_frontend.py
git commit -m "fix: refine profile visual polish"
```

If no defect is found, do not create an empty commit.

- [ ] **Step 8: Hand off the local preview and stop before publication**

Report the local URL, focused/full test results, compile result, unavailable type/lint targets, exact baseline failures, and functional impact. Explicitly note that calculations, calendar geometry, APIs, and other Stats views are unchanged. Wait for the user's visual approval before pushing, commenting on Issue #10, or opening the pull request.
