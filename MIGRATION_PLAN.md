# Writing Studio Analytics: Python -> JavaScript Migration

## Context
The supervisor needs to run the analytics tool themselves but cannot install Python. Distributing a Python package has been unreliable. Goal: a single self-contained HTML file the supervisor opens in any browser - no install, no server, no Python.

The AI chat module (Gemma 3 / local LLM) is being dropped entirely. All other features are preserved: scheduled sessions, walk-in sessions, PII detection, SHA-256 anonymization, PBKDF2-encrypted codebook, PDF export, and the column mapping editor.

The supervisor needs both an **interactive HTML report** (Plotly.js charts) and a **downloadable PDF**.

---

## Tech Stack

| Library | Role | Replaces |
|---|---|---|
| Papa Parse 5.x | CSV parsing | pandas read_csv |
| SheetJS (xlsx) 0.18.x | Excel file support | openpyxl |
| Plotly.js (basic dist) | Interactive charts + PNG export | matplotlib/seaborn |
| jsPDF 2.x | PDF generation | reportlab |
| Web Crypto API (built-in) | SHA-256 + PBKDF2 | Python `cryptography` |
| Danfo.js 1.x | DataFrame groupBy/aggregation | pandas |
| jstat | Welch's t-test, t-distribution CDF | scipy.stats |
| Vite 5.x + vite-plugin-singlefile | Bundle to single HTML file | - |

**No React.** Vanilla JS (ES2022) - the app is a single workflow, not a component tree. Simpler for future maintainers.

---

## Project Structure

```text
writing-studio-analytics-js/
|-- index.html
|-- package.json
|-- vite.config.js
|-- column_mapping.json          # Copied as-is from Python project
`-- src/
    |-- main.js                  # App bootstrap, event wiring
    |-- ui.js                    # Tab switching, progress, error display
    |-- core/
    |   |-- fileLoader.js        # PapaParse + SheetJS, session type detection
    |   |-- columnMapping.js     # loadMapping, validateColumns, normalizeColumns
    |   |-- dataCleaner.js       # Scheduled session cleaning pipeline
    |   |-- walkinCleaner.js     # Walk-in session cleaning pipeline
    |   |-- academicCalendar.js  # Semester detection, academic year labeling
    |   |-- metrics.js           # All scheduled session metrics
    |   |-- walkinMetrics.js     # Walk-in metrics (Gini, temporal, duration)
    |   `-- privacy.js           # PII detection, SHA-256 anon, PBKDF2 codebook
    |-- stats/
    |   `-- statistics.js        # IQR outlier, quantile, Gini, t-test, groupBy helpers
    |-- charts/
    |   |-- scheduledCharts.js   # ~40 Plotly chart builders (<- charts.py)
    |   `-- walkinCharts.js      # Walk-in Plotly charts (<- walkin_charts.py)
    |-- report/
    |   |-- reportBuilder.js     # Renders interactive HTML report panel
    |   |-- pdfExporter.js       # jsPDF: cover -> sections -> embedded chart PNGs
    |   `-- templates.js         # Executive summary text, KPI box HTML
    `-- codebook/
        `-- codebookUI.js        # Codebook Lookup tab UI
```

---

## Critical Files to Migrate (source -> target)

| Python source | JS target | Notes |
|---|---|---|
| `src/core/data_cleaner.py` | `core/dataCleaner.js` | Function-for-function port |
| `src/core/walkin_cleaner.py` | `core/walkinCleaner.js` | Function-for-function port |
| `src/core/metrics.py` + `location_metrics.py` | `core/metrics.js` | pandas -> array + Danfo.js |
| `src/core/walkin_metrics.py` | `core/walkinMetrics.js` | Gini -> statistics.js |
| `src/core/privacy.py` | `core/privacy.js` | Web Crypto API (see notes) |
| `src/utils/academic_calendar.py` | `core/academicCalendar.js` | Straight port |
| `src/visualizations/charts.py` | `charts/scheduledCharts.js` | matplotlib -> Plotly.js |
| `src/visualizations/walkin_charts.py` | `charts/walkinCharts.js` | matplotlib -> Plotly.js |
| `src/visualizations/report_generator.py` | `report/pdfExporter.js` | reportlab -> jsPDF |
| `src/visualizations/walkin_report_generator.py` | `report/pdfExporter.js` | merged into same file |
| `column_mapping.json` | `column_mapping.json` | **Reused verbatim** |
| `src/ai_chat/` (entire folder) | - | **Dropped** |

---

## Key Algorithm Notes

### IQR Outlier Removal (`statistics.js`)
Port from `data_cleaner.py:remove_outliers` and `walkin_cleaner.py:handle_duration_outliers`:
- `lower = max(lowerMin, Q1 - 1.5 * IQR)`, `upper = Q3 + 1.5 * IQR`
- Scheduled sessions: `lowerMin = 0.05` (hours floor); walk-ins: `lowerMin = 0`
- Quantile uses **linear interpolation** to match pandas default

### Gini Coefficient (`statistics.js`)
Port from `walkin_metrics.py:calculate_gini_coefficient`:
```js
function giniCoefficient(values) {
  const sorted = [...values].filter(v => v != null).sort((a,b) => a-b);
  const n = sorted.length;
  let cumsum = 0;
  for (let i = 0; i < n; i++) cumsum += (2*(i+1) - n - 1) * sorted[i];
  const total = sorted.reduce((a,b) => a+b, 0);
  return total === 0 ? 0 : cumsum / (n * total);
}
```

### Welch's T-Test (`statistics.js`)
Use **jstat** for Student-t CDF only; compute Welch statistic and degrees of freedom explicitly so behavior matches SciPy:

```js
t = (mean1 - mean2) / Math.sqrt(var1 / n1 + var2 / n2);
df = ((var1 / n1 + var2 / n2) ** 2) /
     (((var1 / n1) ** 2) / (n1 - 1) + ((var2 / n2) ** 2) / (n2 - 1));
p = 2 * (1 - jStat.studentt.cdf(Math.abs(t), df));
```

Parity requirement: for fixed fixture datasets, `|t_js - t_py| <= 1e-6`, `|df_js - df_py| <= 1e-6`, and `|p_js - p_py| <= 1e-4` vs `scipy.stats.ttest_ind(equal_var=False)`.

### SHA-256 Anonymization (`privacy.js`)
```js
async function sha256Hex(str) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(str));
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2,'0')).join('');
}
// ID: 'STU_' + parseInt(hex.slice(0, 8), 16) % 100000  (matches Python exactly)
```

### PBKDF2 Codebook Encryption (`privacy.js`)
Web Crypto with same params as Python: 100,000 iterations, SHA-256, fixed salt `'writing_studio_analytics_2025'`. **Uses AES-GCM** (not Python's Fernet/AES-CBC - not cross-compatible). Save format: `{ version: 2, iv: "<base64>", ciphertext: "<base64>" }`.

> **Migration note**: Existing `.enc` codebooks from the Python app are not compatible. Any existing codebooks need to be re-created once after switching to the JS app.
>
> **Security tradeoff note**: `version: 2` intentionally keeps a fixed salt for deterministic compatibility with this migration. In a future `version: 3`, move to a random per-file salt stored in the payload (for example `{ version, salt, iv, ciphertext }`) while preserving a `version: 2` decrypt path.

---

## Implementation Phases

| Phase | Scope | Goal |
|---|---|---|
| 1 | `fileLoader.js`, `columnMapping.js`, `main.js`, `ui.js` | File upload + column validation working |
| 2 | `statistics.js`, `academicCalendar.js`, `dataCleaner.js`, `walkinCleaner.js` | Full cleaning pipeline, compare output against Python |
| 3 | `privacy.js`, `codebookUI.js` | PII detection, anonymization, codebook save/load |
| 4 | `metrics.js`, `walkinMetrics.js` | All metrics calculated, t-test + Gini verified |
| 5 | `scheduledCharts.js`, `walkinCharts.js`, `reportBuilder.js` | All charts render interactively |
| 6 | `pdfExporter.js`, `templates.js` | Downloadable PDF with all sections |
| 7 | Column Mapping tab, error handling, polish | Supervisor can fix column names when Penji changes format |
| 8 | `vite build` with `vite-plugin-singlefile` | Single `.html` file, tested by double-click in Chrome + Edge |

## Getting Started: Week 1 Kickoff Plan

1. **Create the JS repo scaffold**
   - Initialize `writing-studio-analytics-js` with Vite (vanilla JS template).
   - Add dependencies from the Tech Stack table.
   - Copy `column_mapping.json` into the new repo root.

2. **Build Phase 1 vertical slice first**
   - Implement `fileLoader.js` for CSV and Excel parsing.
   - Implement `columnMapping.js` validation against required fields.
   - Wire a minimal `main.js` + `ui.js` flow that can:
     - upload file
     - detect session type (scheduled vs walk-in)
     - display column validation pass/fail results

3. **Establish parity fixtures before heavy coding**
   - Export 2-3 representative datasets from the Python app (scheduled, walk-in, mixed edge-case).
   - Save Python reference outputs for cleaning + key metrics as JSON snapshots.
   - Store snapshots under `tests/fixtures/` in the JS repo.

4. **Set up automated checks early**
   - Add Vitest + CI command for local parity checks.
   - Add initial tests for `statistics.js` quantile/IQR/Gini and SHA-256 ID generation.

5. **Demo checkpoint at end of week**
   - Deliver a runnable prototype showing file upload + validation + one sample chart.
   - Confirm the supervisor can open the prototype with no Python installed.

### Week 1 Definition of Done

- New JS repo builds successfully (`npm run build`).
- A test file can be uploaded and validated end-to-end in the browser.
- At least one fixture-based unit test suite is passing.
- Scope and acceptance criteria for Phase 2 are agreed before porting all cleaning logic.

### Phase Exit Criteria

- Phase 2 exit: cleaning output for the golden dataset matches Python on row count, dropped-row IDs, and duration outlier bounds.
- Phase 3 exit: codebook encrypt/decrypt passes round-trip tests; wrong password fails with a handled user-facing error.
- Phase 4 exit: metric snapshot JSON matches Python within declared tolerances, including Welch `t`, `df`, and `p`.
- Phase 5 exit: chart checklist complete (all expected chart IDs render; no empty traces for non-empty inputs).
- Phase 6 exit: PDF checklist complete (section order, KPI values, and chart image embedding verified).
- Phase 8 exit: offline open via `file://` succeeds on target browsers and completes the full workflow end-to-end.

---

## Distribution

```js
// vite.config.js
import { viteSingleFile } from 'vite-plugin-singlefile';
export default { plugins: [viteSingleFile()], build: { cssCodeSplit: false } };
```

Output: `dist/index.html` (~5.5 MB with all JS inlined). Rename to `writing-studio-analytics.html` and send to supervisor. No server needed.

> **Safari note**: Validate all Web Crypto and file download flows on Safari during Phase 7. If it fails, document the exact failure and require Chrome or Edge for production use.

---

## Verification

1. **Unit tests** (Vitest): `statistics.js` functions against known Python outputs - quantile, Gini, IQR bounds, SHA-256 ID for a known email.
2. **Golden dataset comparison**: Run both apps on same CSV; compare attendance rates, mean satisfaction, mean lead time, Gini, t-test p-values, top-10 tutor counts. Tolerance: +/- 0.01.
3. **PDF visual check**: Compare downloaded JS PDF against Python PDF - section order, chart presence, key numbers.
4. **Codebook round-trip**: Encrypt a known mapping, decrypt with correct password, verify entries; confirm wrong password fails.
5. **Distribution test**: Open `writing-studio-analytics.html` by double-click on a machine with no Python/Node. Confirm full workflow in Chrome and Edge.
6. **Welch parity fixtures**: For at least 5 fixed numeric fixtures (balanced, unbalanced, equal means, unequal variances, small n), compare JS vs SciPy values for `t`, `df`, and `p` using the tolerances above.
7. **Browser matrix acceptance**:
   - Chrome (latest stable on Windows): pass
   - Edge (latest stable on Windows): pass
   - Safari (latest stable on macOS): run and record result
8. **Crypto API smoke checks per browser**: verify `crypto.subtle.digest`, `deriveKey(PBKDF2)`, `encrypt/decrypt(AES-GCM)`, and file download APIs used by codebook and PDF paths.
