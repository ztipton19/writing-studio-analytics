/**
 * ui.js
 *
 * Tab switching, progress bar, alert messages, and validation result rendering.
 * All DOM manipulation lives here; business logic lives in core/*.js.
 *
 * Public API:
 *   initTabs()
 *   enableTab(tabId)
 *   switchTab(tabId)
 *   setProgress(pct, label)
 *   showProgress()
 *   hideProgress()
 *   showAlert(message, type)   type: 'error'|'warning'|'success'|'info'
 *   clearAlerts()
 *   renderValidationResult(result, sessionType, fileName, rowCount)
 *   showProceedButton(onClick)
 *   hideProceedButton()
 */

// ---------------------------------------------------------------------------
// Tab management
// ---------------------------------------------------------------------------

/** @type {Map<string, HTMLElement>} */
const _tabPanels = new Map();
/** @type {Map<string, HTMLButtonElement>} */
const _tabButtons = new Map();

/**
 * Wire up tab buttons and panels.
 * Must be called once on DOMContentLoaded.
 */
export function initTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    const tabId = btn.dataset.tab;
    _tabButtons.set(tabId, btn);
    btn.addEventListener('click', () => {
      if (!btn.disabled) switchTab(tabId);
    });
  });

  document.querySelectorAll('.tab-panel').forEach(panel => {
    const id = panel.id.replace('tab-', '');
    _tabPanels.set(id, panel);
  });
}

/**
 * Activate a tab panel and update button states.
 * @param {string} tabId
 */
export function switchTab(tabId) {
  _tabPanels.forEach((panel, id) => {
    panel.classList.toggle('active', id === tabId);
  });
  _tabButtons.forEach((btn, id) => {
    btn.classList.toggle('active', id === tabId);
  });
}

/**
 * Enable a disabled tab (e.g. after a file is successfully processed).
 * @param {string} tabId
 */
export function enableTab(tabId) {
  const btn = _tabButtons.get(tabId);
  if (btn) btn.disabled = false;
}

// ---------------------------------------------------------------------------
// Progress bar
// ---------------------------------------------------------------------------

export function showProgress() {
  const el = document.getElementById('progress-container');
  if (el) el.style.display = 'block';
}

export function hideProgress() {
  const el = document.getElementById('progress-container');
  if (el) el.style.display = 'none';
}

/**
 * @param {number} pct   - 0–100
 * @param {string} label
 */
export function setProgress(pct, label) {
  const fill = document.getElementById('progress-bar-fill');
  const lbl = document.getElementById('progress-label');
  if (fill) fill.style.width = `${Math.min(100, Math.max(0, pct))}%`;
  if (lbl) lbl.textContent = label ?? '';
}

// ---------------------------------------------------------------------------
// Alerts
// ---------------------------------------------------------------------------

/** @type {string[]} valid alert types */
const ALERT_TYPES = ['error', 'warning', 'success', 'info'];

const ALERT_ICONS = {
  error: '❌',
  warning: '⚠️',
  success: '✅',
  info: 'ℹ️',
};

/**
 * Show an alert banner above the validation card.
 * @param {string} message
 * @param {'error'|'warning'|'success'|'info'} [type='info']
 */
export function showAlert(message, type = 'info') {
  const area = document.getElementById('alert-area');
  if (!area) return;

  const safeType = ALERT_TYPES.includes(type) ? type : 'info';
  const div = document.createElement('div');
  div.className = `alert alert-${safeType}`;
  const icon = document.createElement('span');
  icon.textContent = ALERT_ICONS[safeType];
  const text = document.createElement('span');
  text.textContent = message;
  div.appendChild(icon);
  div.appendChild(text);
  area.appendChild(div);
}

/** Remove all alert banners. */
export function clearAlerts() {
  const area = document.getElementById('alert-area');
  if (area) area.innerHTML = '';
}

// ---------------------------------------------------------------------------
// Validation result rendering
// ---------------------------------------------------------------------------

/**
 * Render the validation card with column-level results and dataset summary.
 *
 * @param {import('./core/columnMapping.js').ValidationResult} result
 * @param {'scheduled'|'walkin'|'unknown'} sessionType
 * @param {string} fileName
 * @param {number} rowCount
 */
export function renderValidationResult(result, sessionType, fileName, rowCount) {
  const card = document.getElementById('validation-card');
  if (!card) return;

  // Title
  const title = document.getElementById('validation-title');
  const typeLabel = sessionType === 'scheduled'
    ? 'Scheduled Sessions'
    : sessionType === 'walkin'
      ? 'Walk-in Sessions'
      : 'Unknown Type';

  const statusBadge = result.valid
    ? `<span class="badge badge-green">✓ Valid</span>`
    : `<span class="badge badge-red">✗ Missing required columns</span>`;

  title.innerHTML = `${fileName} · ${typeLabel} ${statusBadge}`;

  // Summary KPIs
  const grid = document.getElementById('summary-grid');
  grid.innerHTML = _kpi(rowCount.toLocaleString(), 'Rows') +
    _kpi(result.presentRequired.length + result.presentOptional.length, 'Columns found') +
    _kpi(result.missingRequired.length, 'Required missing', result.missingRequired.length > 0 ? '#dc2626' : undefined) +
    _kpi(result.extraColumns.length, 'Unmapped columns');

  // Required columns
  const reqList = document.getElementById('required-list');
  reqList.innerHTML = '';

  const allRequired = [...result.presentRequired, ...result.missingRequired];
  if (allRequired.length === 0) {
    reqList.innerHTML = '<span style="color:#888;font-size:12px">No required columns defined for this session type.</span>';
  } else {
    result.presentRequired.forEach(col => {
      reqList.appendChild(_pill(col, 'ok'));
    });
    result.missingRequired.forEach(col => {
      reqList.appendChild(_pill(col, 'missing'));
    });
  }

  // Optional present
  const optList = document.getElementById('optional-list');
  optList.innerHTML = '';
  result.presentOptional.forEach(col => {
    optList.appendChild(_pill(col, 'ok'));
  });
  if (result.extraColumns.length > 0) {
    result.extraColumns.forEach(col => {
      optList.appendChild(_pill(col, 'extra'));
    });
  }
  if (result.presentOptional.length === 0 && result.extraColumns.length === 0) {
    optList.innerHTML = '<span style="color:#888;font-size:12px">None</span>';
  }

  // Missing optional
  const missingOptSec = document.getElementById('missing-optional-section');
  const missingOptList = document.getElementById('missing-optional-list');
  if (result.missingOptional.length > 0) {
    missingOptSec.style.display = '';
    missingOptList.innerHTML = '';
    result.missingOptional.forEach(col => {
      missingOptList.appendChild(_pill(col, 'missing'));
    });
  } else {
    missingOptSec.style.display = 'none';
  }

  card.style.display = 'block';
}

// ---------------------------------------------------------------------------
// Proceed button
// ---------------------------------------------------------------------------

export function showProceedButton(onClick) {
  const btn = document.getElementById('proceed-btn');
  if (!btn) return;
  btn.style.display = 'block';
  // Remove any previous listener by cloning
  const fresh = btn.cloneNode(true);
  btn.replaceWith(fresh);
  fresh.addEventListener('click', onClick);
}

export function hideProceedButton() {
  const btn = document.getElementById('proceed-btn');
  if (btn) btn.style.display = 'none';
}

// ---------------------------------------------------------------------------
// Private helpers
// ---------------------------------------------------------------------------

function _kpi(value, label, color) {
  const style = color ? `style="color:${color}"` : '';
  return `<div class="summary-kpi">
    <div class="kpi-val" ${style}>${value}</div>
    <div class="kpi-lbl">${label}</div>
  </div>`;
}

/**
 * @param {string} text
 * @param {'ok'|'missing'|'extra'} kind
 */
function _pill(text, kind) {
  const cls = kind === 'ok'
    ? 'col-pill-ok'
    : kind === 'missing'
      ? 'col-pill-missing'
      : 'col-pill-extra';
  const el = document.createElement('span');
  el.className = `col-pill ${cls}`;
  el.textContent = text;
  return el;
}
