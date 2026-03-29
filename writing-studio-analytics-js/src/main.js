/**
 * main.js
 *
 * Application bootstrap.
 * Wires together file upload events → fileLoader → columnMapping → ui.
 *
 * This is the only module that touches the DOM directly for event binding;
 * all rendering is delegated to ui.js.
 */

import { loadFile } from './core/fileLoader.js';
import { loadMapping, validateColumns, normalizeColumns } from './core/columnMapping.js';
import {
  initTabs,
  enableTab,
  switchTab,
  setProgress,
  showProgress,
  hideProgress,
  showAlert,
  clearAlerts,
  renderValidationResult,
  showProceedButton,
  hideProceedButton,
} from './ui.js';

// ---------------------------------------------------------------------------
// App state
// ---------------------------------------------------------------------------

/** @type {{ rows: object[], headers: string[], sessionType: string } | null} */
let _processedData = null;

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  bindUploadZone();
});

// ---------------------------------------------------------------------------
// Upload zone
// ---------------------------------------------------------------------------

function bindUploadZone() {
  const zone = document.getElementById('upload-zone');
  const input = document.getElementById('file-input');

  if (!zone || !input) return;

  // Click to browse
  zone.addEventListener('click', () => input.click());
  zone.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      input.click();
    }
  });

  // File input change
  input.addEventListener('change', () => {
    if (input.files && input.files[0]) {
      handleFile(input.files[0]);
      // Reset so the same file can be re-uploaded
      input.value = '';
    }
  });

  // Drag-and-drop
  zone.addEventListener('dragover', e => {
    e.preventDefault();
    zone.classList.add('drag-over');
  });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('drag-over');
    const file = e.dataTransfer?.files?.[0];
    if (file) handleFile(file);
  });
}

// ---------------------------------------------------------------------------
// File handling pipeline
// ---------------------------------------------------------------------------

/**
 * Full pipeline: parse → validate → display results.
 * @param {File} file
 */
async function handleFile(file) {
  clearAlerts();
  hideProceedButton();

  // Reset validation card visibility
  const card = document.getElementById('validation-card');
  if (card) card.style.display = 'none';

  showProgress();
  setProgress(10, `Loading "${file.name}"…`);

  try {
    // Step 1: parse
    const { rows, headers, sessionType, fileName, rowCount } = await loadFile(file);
    setProgress(40, 'Detecting session type…');

    if (sessionType === 'unknown') {
      showAlert(
        'Could not detect session type (scheduled vs walk-in). ' +
        'Check that the file is a valid Penji export. Validation will use the scheduled mapping.',
        'warning'
      );
    }

    setProgress(60, 'Validating columns…');

    // Step 2: load mapping and validate
    const mapping = await loadMapping();
    const effectiveType = sessionType === 'unknown' ? 'scheduled' : sessionType;
    const validationResult = validateColumns(headers, effectiveType, mapping);

    setProgress(80, 'Normalising column names…');

    // Step 3: normalise column names to canonical targets
    const { rows: normRows, headers: normHeaders } = normalizeColumns(
      rows,
      headers,
      validationResult.sourceToTarget
    );

    setProgress(100, 'Done');
    hideProgress();

    // Step 4: render results
    if (!validationResult.valid) {
      showAlert(
        `Missing required column(s): ${validationResult.missingRequired.join(', ')}. ` +
        'Use the Column Mapping tab to remap column names if Penji changed its export format.',
        'error'
      );
    } else {
      showAlert(`"${fileName}" loaded successfully — ${rowCount.toLocaleString()} rows.`, 'success');
    }

    renderValidationResult(validationResult, effectiveType, fileName, rowCount);

    // Store processed data for downstream phases
    _processedData = {
      rows: normRows,
      headers: normHeaders,
      sessionType: effectiveType,
      fileName,
      rowCount,
    };

    // Show proceed button only when required columns are present
    if (validationResult.valid) {
      showProceedButton(() => {
        enableTab('report');
        switchTab('report');
      });
    }

  } catch (err) {
    hideProgress();
    showAlert(err.message, 'error');
    console.error('[WritingStudioAnalytics]', err);
  }
}

// ---------------------------------------------------------------------------
// Expose processed data for future phases (charts, metrics, etc.)
// ---------------------------------------------------------------------------

export function getProcessedData() {
  return _processedData;
}
