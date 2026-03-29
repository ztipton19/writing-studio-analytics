/**
 * fileLoader.js
 *
 * Parses CSV (PapaParse) and Excel (SheetJS) exports from Penji.
 * Detects whether the dataset is 'scheduled', 'walkin', or 'unknown'.
 *
 * Public API:
 *   loadFile(file)  → Promise<{ rows, headers, sessionType, fileName }>
 */

import Papa from 'papaparse';
import * as XLSX from 'xlsx';

// ---------------------------------------------------------------------------
// Session-type detection  (mirrors data_cleaner.py:detect_session_type)
// ---------------------------------------------------------------------------

/** Column substrings that indicate scheduled-session exports from Penji. */
const SCHEDULED_INDICATORS = [
  'Appointment Type',
  'Requested Length',
  'Student - On a scale of 1-5',
];

/** Column substrings that indicate walk-in exports from Penji. */
const WALKIN_INDICATORS = [
  'Duration Minutes',
  'Check In At Date',
  'Check In At Time',
];

/**
 * Infer session type from column headers.
 * @param {string[]} headers - Column names (already stripped of whitespace)
 * @returns {'scheduled'|'walkin'|'unknown'}
 */
export function detectSessionType(headers) {
  const scheduledScore = SCHEDULED_INDICATORS.filter(ind =>
    headers.some(h => h.includes(ind))
  ).length;

  const walkinScore = WALKIN_INDICATORS.filter(ind =>
    headers.some(h => h.includes(ind))
  ).length;

  if (scheduledScore >= 2) return 'scheduled';
  if (walkinScore >= 2) return 'walkin';

  // Single-indicator fallback
  if (walkinScore >= 1 && scheduledScore === 0) return 'walkin';
  if (scheduledScore >= 1 && walkinScore === 0) return 'scheduled';

  return 'unknown';
}

// ---------------------------------------------------------------------------
// Column normalisation  (mirrors data_cleaner.py:clean_column_names)
// ---------------------------------------------------------------------------

/**
 * Strip leading/trailing whitespace from every column name.
 * Penji exports often have trailing spaces that break matching.
 * @param {string[]} headers
 * @returns {string[]}
 */
export function cleanColumnNames(headers) {
  return headers.map(h => (typeof h === 'string' ? h.trim() : String(h).trim()));
}

// ---------------------------------------------------------------------------
// CSV parsing  (PapaParse)
// ---------------------------------------------------------------------------

/**
 * Parse a CSV File object.
 * @param {File} file
 * @returns {Promise<{ rows: object[], headers: string[] }>}
 */
function parseCSV(file) {
  return new Promise((resolve, reject) => {
    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      transformHeader: h => (typeof h === 'string' ? h.trim() : String(h).trim()),
      complete(results) {
        if (results.errors.length > 0) {
          // Non-fatal parse warnings — log them but continue
          const fatal = results.errors.filter(e => e.type === 'Quotes' || e.type === 'FieldMismatch');
          if (fatal.length > 0) {
            reject(new Error(`CSV parse error: ${fatal[0].message} (row ${fatal[0].row})`));
            return;
          }
        }
        const headers = results.meta.fields ?? [];
        resolve({ rows: results.data, headers });
      },
      error(err) {
        reject(new Error(`CSV parse failed: ${err.message}`));
      },
    });
  });
}

// ---------------------------------------------------------------------------
// Excel parsing  (SheetJS)
// ---------------------------------------------------------------------------

/**
 * Parse an Excel (.xlsx / .xls) File object.
 * Reads the first worksheet.
 * @param {File} file
 * @returns {Promise<{ rows: object[], headers: string[] }>}
 */
function parseExcel(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = event => {
      try {
        const data = new Uint8Array(event.target.result);
        const workbook = XLSX.read(data, { type: 'array', cellDates: true });
        const sheetName = workbook.SheetNames[0];
        if (!sheetName) {
          reject(new Error('Excel file contains no worksheets.'));
          return;
        }
        const sheet = workbook.Sheets[sheetName];
        // Convert to JSON; raw:false → formatted strings for dates
        const jsonRows = XLSX.utils.sheet_to_json(sheet, {
          defval: '',
          raw: false,
        });

        if (jsonRows.length === 0) {
          resolve({ rows: [], headers: [] });
          return;
        }

        // Trim header keys to match CSV behaviour
        const rawHeaders = Object.keys(jsonRows[0]);
        const headers = cleanColumnNames(rawHeaders);

        // Re-key every row with trimmed headers
        const rows = jsonRows.map(row => {
          const cleaned = {};
          rawHeaders.forEach((raw, i) => {
            cleaned[headers[i]] = row[raw];
          });
          return cleaned;
        });

        resolve({ rows, headers });
      } catch (err) {
        reject(new Error(`Excel parse failed: ${err.message}`));
      }
    };
    reader.onerror = () => reject(new Error('FileReader error reading Excel file.'));
    reader.readAsArrayBuffer(file);
  });
}

// ---------------------------------------------------------------------------
// Public entry point
// ---------------------------------------------------------------------------

/**
 * Load and parse a Penji export file (CSV or Excel).
 *
 * @param {File} file - Browser File object from <input type="file"> or drag-drop
 * @returns {Promise<{
 *   rows: object[],
 *   headers: string[],
 *   sessionType: 'scheduled'|'walkin'|'unknown',
 *   fileName: string,
 *   rowCount: number
 * }>}
 * @throws {Error} on unsupported file type or parse failure
 */
export async function loadFile(file) {
  const name = file.name.toLowerCase();
  let rows, headers;

  if (name.endsWith('.csv')) {
    ({ rows, headers } = await parseCSV(file));
  } else if (name.endsWith('.xlsx') || name.endsWith('.xls')) {
    ({ rows, headers } = await parseExcel(file));
  } else {
    throw new Error(
      `Unsupported file type: "${file.name}". Please upload a CSV or Excel file.`
    );
  }

  // Always re-clean headers (CSV transformer may have missed edge cases)
  headers = cleanColumnNames(headers);
  const sessionType = detectSessionType(headers);

  return {
    rows,
    headers,
    sessionType,
    fileName: file.name,
    rowCount: rows.length,
  };
}
