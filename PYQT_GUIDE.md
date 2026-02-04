# PyQt Dashboard Migration Guide

## Git Strategy

Before touching any code, branch off main:

```bash
git checkout -b pyqt-dashboard
```

All work happens here. `main` stays untouched and fully functional. When the
dashboard is done and tested, you merge (or just keep both — the PDF pipeline
and the dashboard are independent products). Nothing in `src/core/` or
`src/visualizations/charts.py` needs to change for the dashboard to work.

---

## What Stays the Same (don't touch these)

The entire backend is reusable as-is. The Streamlit UI is just a thin layer
on top of these — swap that layer out, everything underneath carries over.

| Module | Role | Changes needed |
|---|---|---|
| `src/core/data_cleaner.py` | 13-step cleaning pipeline | None |
| `src/core/metrics.py` | Calculates all 14 metric categories | None |
| `src/core/privacy.py` | Anonymization + codebook encryption | None |
| `src/visualizations/charts.py` | All 30+ chart functions | None (see note on figsize below) |
| `src/utils/academic_calendar.py` | Semester detection/labeling | None |
| `src/ai_chat/` | Gemma chat handler | None (just wire it into a tab) |
| `courses.csv` | Course reference data | None |

**figsize note:** The chart functions hardcode `figsize=PAGE_LANDSCAPE` (11x8.5).
When embedded in PyQt via `FigureCanvasQTAgg`, the canvas scales the figure to
fit the widget — the hardcoded figsize doesn't matter visually. The charts will
fill whatever space the tab gives them. No changes needed to chart functions.

---

## What Gets Built New

A single new file: the PyQt application window. It replaces `app.py` (the
Streamlit UI) but nothing else. Everything it needs already exists in `src/`.

```
src/
└── dashboard/
    └── main.py          ← the new PyQt app (this is the only new file)
```

---

## Tab Layout

Maps directly to the existing PDF sections. Each tab is a scroll area
containing one or more matplotlib charts rendered via `FigureCanvasQTAgg`.

| Tab | Charts pulled from `charts.py` | Conditional? |
|---|---|---|
| **Overview** | `plot_sessions_over_time`, key metrics displayed as text cards, `plot_semester_metrics_comparison` | Semester comparison only if 2+ semesters |
| **Booking & Attendance** | `plot_booking_lead_time_donut`, `plot_sessions_by_day_of_week`, `plot_sessions_heatmap_day_time`, `plot_session_outcomes_pie`, `plot_no_show_by_day`, `plot_outcomes_over_time` | |
| **Students** | `plot_top_active_students`, `plot_first_time_vs_returning`, `plot_student_retention_trends` | |
| **Satisfaction** | `plot_confidence_comparison`, `plot_confidence_change_distribution`, `plot_satisfaction_distribution`, `plot_satisfaction_trends` | |
| **Tutors** | `plot_sessions_per_tutor`, `plot_tutor_workload_balance`, `plot_session_length_by_tutor` | |
| **Session Content** | `plot_writing_stages`, `plot_focus_areas`, `plot_course_table` | Course table only if `courses.csv` match found |
| **Incentives** | `plot_incentive_breakdown`, `plot_incentives_vs_tutor_rating`, `plot_incentives_vs_satisfaction` | Entire tab only if `Incentivized` column exists |
| **Data Quality** | `plot_survey_response_rates`, `plot_missing_data_concern` | |
| **AI Chat** | ChatHandler from `src/ai_chat/` | Only if model is loaded |

---

## Implementation Order

Do these in order. Each step is testable before moving to the next.

### Step 1: Skeleton window with file upload

- `QMainWindow` with a `QTabWidget`
- A toolbar or menu with "Open File" (`QFileDialog.getOpenFileName`)
- A status bar that shows what's loaded (row count, date range)
- No charts yet — just tabs with placeholder labels

### Step 2: Wire in the data pipeline

- On file open: run `clean_data()` → `calculate_all_metrics()` → store both
- Show a success/failure message
- This is the exact same call chain as `app.py` — just triggered by a button
  instead of Streamlit's file upload widget

### Step 3: Render charts into tabs

- For each tab, call the relevant `plot_*()` functions (they return `fig`)
- Embed each `fig` into a `FigureCanvasQTAgg` inside a `QScrollArea`
- Start with the Overview tab, verify it renders, then do the rest

### Step 4: Add conditional tabs

- Incentives tab: only add if `Incentivized` column exists in the cleaned df
- Semester comparison: only show if 2+ semesters detected
- AI Chat tab: only add if model loads successfully
- Course table: only show if course codes match `courses.csv`

### Step 5: Add PDF export

- Keep the existing `generate_full_report()` call exactly as-is
- Add an "Export PDF" button to the toolbar
- On click: call `generate_full_report(df, cleaning_log, output_path)`
- The PDF pipeline is completely independent of the dashboard UI

### Step 6: Package with PyInstaller

See packaging section below.

---

## Key PyQt Patterns for This App

### Embedding a matplotlib figure in a tab

```python
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QScrollArea

def add_chart_to_layout(layout, fig):
    """Takes a matplotlib fig, embeds it in the given QVBoxLayout."""
    canvas = FigureCanvasQTAgg(fig)
    canvas.setMinimumHeight(500)
    layout.addWidget(canvas)
```

Every `plot_*()` function returns a `fig` or `None`. The pattern is:

```python
fig = plot_writing_stages(df)
if fig:
    add_chart_to_layout(tab_layout, fig)
```

### Scrollable tab with multiple charts

```python
scroll = QScrollArea()
scroll.setWidgetResizable(True)
container = QWidget()
layout = QVBoxLayout(container)
scroll.setWidget(container)

# Add charts to layout
fig1 = plot_writing_stages(df)
if fig1: add_chart_to_layout(layout, fig1)

fig2 = plot_focus_areas(df)
if fig2: add_chart_to_layout(layout, fig2)

# Add scroll area to the tab
tab_widget.addTab(scroll, "Session Content")
```

### Overview tab: key metrics as text cards

The `create_key_metrics_summary()` function returns a dict. Display these as
simple `QLabel` widgets in a grid above the first chart:

```python
summary = create_key_metrics_summary(df, context)
# summary['total_sessions'], summary['completion_rate'], etc.
```

---

## PyInstaller Packaging

### Install

```bash
pip install pyinstaller PyQt5
```

### Run

```bash
pyinstaller --onefile --windowed src/dashboard/main.py
  --add-data "src:src"
  --add-data "courses.csv:."
  --add-data "models:models"
  --hidden-import matplotlib.backends.backend_qt5agg
  --hidden-import PyQt5.QtGui
  --hidden-import PyQt5.QtCore
```

### What `--add-data` does

- `src:src` — bundles your entire `src/` package so imports work inside the exe
- `courses.csv:.` — the course reference file lands next to the exe
- `models:models` — the Gemma model (you already have this working)

### Known gotchas

- **matplotlib backend:** Must set `matplotlib.use('Qt5Agg')` at the very top
  of `main.py`, before any other matplotlib import. If this is wrong the app
  will crash on launch.
- **First run is slow:** PyInstaller exe takes a few seconds to unpack on first
  launch. Normal.
- **Model loading:** If AI Chat tab is included, model load time adds several
  seconds at startup. Consider loading it lazily (only when the user clicks the
  AI Chat tab for the first time).

---

## New Dependencies to Add

Add these to `requirements.txt`:

```
PyQt5>=5.15.0
pyinstaller>=6.0.0
```

Everything else you already have.

---

## What the Streamlit app (`app.py`) becomes

Nothing. It stays. It's still there on `main` if you ever want to revisit
cloud/hosted deployment later (with a FERPA-compliant host). The PyQt dashboard
is a parallel product, not a replacement. Two entry points, same backend:

- `app.py` → Streamlit (web, for hosted use)
- `src/dashboard/main.py` → PyQt (packaged exe, for your supervisor)
