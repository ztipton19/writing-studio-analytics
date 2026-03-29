/**
 * codebookUI.js
 *
 * Codebook tab UI — lookup and info display.
 * Wired into the Codebook tab in index.html.
 *
 * Public API:
 *   initCodebookUI()   — call once on DOMContentLoaded
 */

import {
  lookupInCodebook,
  getCodebookInfo,
} from '../core/privacy.js';

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------

export function initCodebookUI() {
  bindLookupForm();
  bindInfoForm();
}

// ---------------------------------------------------------------------------
// Lookup form — reverse-lookup anonymous ID → email
// ---------------------------------------------------------------------------

function bindLookupForm() {
  const form = document.getElementById('cb-lookup-form');
  if (!form) return;

  form.addEventListener('submit', async e => {
    e.preventDefault();
    const fileInput  = document.getElementById('cb-lookup-file');
    const anonInput  = document.getElementById('cb-lookup-id');
    const pwdInput   = document.getElementById('cb-lookup-pwd');
    const resultEl   = document.getElementById('cb-lookup-result');

    clearResult(resultEl);

    const file    = fileInput?.files?.[0];
    const anonId  = anonInput?.value?.trim();
    const password = pwdInput?.value ?? '';

    if (!file) {
      showResult(resultEl, 'Please upload a codebook file.', 'error');
      return;
    }
    if (!anonId) {
      showResult(resultEl, 'Please enter a student or tutor ID.', 'error');
      return;
    }
    if (!password) {
      showResult(resultEl, 'Please enter the codebook password.', 'error');
      return;
    }

    let payloadStr;
    try {
      payloadStr = await file.text();
    } catch {
      showResult(resultEl, 'Could not read the codebook file.', 'error');
      return;
    }

    try {
      const email = await lookupInCodebook(anonId, payloadStr, password);
      showResult(resultEl,
        `<strong>${escHtml(anonId)}</strong> → <code>${escHtml(email)}</code>`,
        'success',
        true
      );
    } catch (err) {
      showResult(resultEl, err.message, 'error');
    }
  });
}

// ---------------------------------------------------------------------------
// Info form — display codebook metadata (no individual entries)
// ---------------------------------------------------------------------------

function bindInfoForm() {
  const form = document.getElementById('cb-info-form');
  if (!form) return;

  form.addEventListener('submit', async e => {
    e.preventDefault();
    const fileInput = document.getElementById('cb-info-file');
    const pwdInput  = document.getElementById('cb-info-pwd');
    const resultEl  = document.getElementById('cb-info-result');

    clearResult(resultEl);

    const file     = fileInput?.files?.[0];
    const password = pwdInput?.value ?? '';

    if (!file) {
      showResult(resultEl, 'Please upload a codebook file.', 'error');
      return;
    }
    if (!password) {
      showResult(resultEl, 'Please enter the codebook password.', 'error');
      return;
    }

    let payloadStr;
    try {
      payloadStr = await file.text();
    } catch {
      showResult(resultEl, 'Could not read the codebook file.', 'error');
      return;
    }

    try {
      const info = await getCodebookInfo(payloadStr, password);
      showResult(resultEl, formatInfo(info), 'success', true);
    } catch (err) {
      showResult(resultEl, err.message, 'error');
    }
  });
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * @param {object} info
 * @returns {string} HTML
 */
function formatInfo(info) {
  const rows = [
    ['Session type',   info.session_type],
    ['Total students', info.total_students],
    ['Total tutors',   info.total_tutors],
    ['Created',        info.created],
    ['Date range',     info.date_range],
  ];
  const rowsHtml = rows
    .map(([k, v]) => `<tr><th style="text-align:left;padding:4px 12px 4px 0;color:#555;font-weight:600">${escHtml(String(k))}</th><td style="padding:4px 0">${escHtml(String(v))}</td></tr>`)
    .join('');
  return `<table style="border-collapse:collapse;width:100%">${rowsHtml}</table>`;
}

/**
 * @param {HTMLElement} el
 * @param {string} html
 * @param {'success'|'error'|'info'} type
 * @param {boolean} [isHtml=false]
 */
function showResult(el, html, type, isHtml = false) {
  if (!el) return;
  el.style.display = 'block';
  el.className = `cb-result cb-result-${type}`;
  if (isHtml) {
    el.innerHTML = html;
  } else {
    el.textContent = html;
  }
}

function clearResult(el) {
  if (!el) return;
  el.style.display = 'none';
  el.textContent = '';
}

/** Minimal HTML escaping */
function escHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
