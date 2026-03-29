/**
 * walkinCleaner.js
 *
 * Cleaning pipeline for walk-in (drop-in) sessions.
 * Function-for-function port of src/core/walkin_cleaner.py.
 *
 * Input:  raw rows[] from fileLoader (column names already trimmed by Phase 1)
 * Output: { rows, log }
 *
 * Public API:
 *   cleanWalkinData(rows)  → { rows, log }
 */

import { iqrOutlierBounds } from '../stats/statistics.js';
import { detectSemester, getAcademicYear, getSemesterLabel } from './academicCalendar.js';

// ---------------------------------------------------------------------------
// Step 1: Parse walk-in datetime columns
// ---------------------------------------------------------------------------

const WALKIN_DATETIME_PAIRS = [
  ['Check In At Date',  'Check In At Time',  'Check_In_DateTime'],
  ['Started At Date',   'Started At Time',   'Started_DateTime'],
  ['Ended At Date',     'Ended At Time',     'Ended_DateTime'],
  ['Cancelled At Date', 'Cancelled At Time', 'Cancelled_DateTime'],
];

/**
 * @param {string} dateStr
 * @param {string} timeStr
 * @returns {Date|null}
 */
function parsePair(dateStr, timeStr) {
  const ds = String(dateStr ?? '').trim();
  const ts = String(timeStr ?? '').trim();
  if (!ds || !ts) return null;
  const d = new Date(`${ds} ${ts}`);
  return isNaN(d.getTime()) ? null : d;
}

/** @param {object[]} rows @returns {object[]} */
export function parseWalkinDatetimes(rows) {
  return rows.map(row => {
    const extra = {};
    for (const [datCol, timCol, newCol] of WALKIN_DATETIME_PAIRS) {
      if (datCol in row && timCol in row) {
        extra[newCol] = parsePair(row[datCol], row[timCol]);
      }
    }
    return { ...row, ...extra };
  });
}

// ---------------------------------------------------------------------------
// Step 2: Consolidate course categories
// ---------------------------------------------------------------------------

/**
 * Mirrors walkin_cleaner.py:consolidate_courses course_mapping.
 */
const COURSE_MAPPING = {
  'Other topic not listed': 'Other',
  'Other topic not listed (please describe in intake form in "Is there anything else you\'d like to share?")': 'Other',
  'Speech outlineSpeech outline': 'Speech outline',
  'Scientific or lab reportScientific or lab report': 'Scientific or lab report',
  'Reflection or response paperReflection or response paper': 'Reflection or response paper',
  'Thesis or dissertation (Undergraduate/Graduate)': 'Thesis or dissertation',
  'Thesis or dissertation (Undergradaute/Graduate)': 'Thesis or dissertation',
  'XXXX': 'N/A',
  'Reflection paper': 'Reflection or response paper',
  'Response paper': 'Reflection or response paper',
  'Analysis Paper': 'Analysis Paper: Historical Sources',
  'Professional writing': 'Professional or technical writing assignment',
  'Application essay (scholarship, graduate school, SOP, etc.)': 'Application essay',
};

/** @param {object[]} rows @returns {object[]} */
export function consolidateCourses(rows) {
  return rows.map(row => {
    if (!('Course' in row) || row.Course == null) return row;
    const raw = String(row.Course).trim();
    const mapped = COURSE_MAPPING[raw] ?? raw;
    return { ...row, Course: mapped };
  });
}

// ---------------------------------------------------------------------------
// Step 3: Handle duration outliers (IQR, lowerMin = 3 minutes)
// ---------------------------------------------------------------------------

const WALKIN_LOWER_MIN = 3; // minutes — matches walkin_cleaner.py

/**
 * @param {object[]} rows
 * @returns {{ rows: object[], stats: object }}
 */
export function handleDurationOutliers(rows) {
  const colName = 'Duration Minutes';
  const original = rows.length;

  // Treat empty string as missing (same as null/undefined)
  const isBlank = v => v == null || v === '';

  const values = rows
    .map(r => r[colName])
    .filter(v => !isBlank(v) && !isNaN(Number(v)))
    .map(Number);

  const stats = {
    removedCount: 0, removedPct: 0,
    lowerBound: WALKIN_LOWER_MIN, upperBound: Infinity,
    method: 'iqr', originalCount: original, finalCount: original,
  };

  if (values.length === 0) return { rows, stats };

  const { lower, upper } = iqrOutlierBounds(values, WALKIN_LOWER_MIN);
  stats.lowerBound = Math.round(lower * 1e4) / 1e4;
  stats.upperBound = Math.round(upper * 1e4) / 1e4;

  const cleaned = rows.filter(row => {
    const v = row[colName];
    if (isBlank(v) || isNaN(Number(v))) return true; // keep blank/NaN rows
    const n = Number(v);
    return n >= lower && n <= upper;
  });

  const removedCount = original - cleaned.length;
  stats.removedCount = removedCount;
  stats.removedPct   = original > 0 ? (removedCount / original) * 100 : 0;
  stats.finalCount   = cleaned.length;

  return { rows: cleaned, stats };
}

// ---------------------------------------------------------------------------
// Step 4: Add derived fields
// ---------------------------------------------------------------------------

const DAY_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

/** @param {object[]} rows @returns {object[]} */
export function addDerivedFields(rows) {
  return rows.map(row => {
    const out = { ...row };

    const checkIn = out.Check_In_DateTime;
    if (checkIn instanceof Date && !isNaN(checkIn)) {
      out.Semester       = detectSemester(checkIn);
      out.Academic_Year  = getAcademicYear(checkIn);
      out.Semester_Label = getSemesterLabel(checkIn);
      out.Day_of_Week    = DAY_NAMES[checkIn.getDay()];
      out.Hour_of_Day    = checkIn.getHours();
    }

    // Wait time: check-in → session start
    if (
      out.Check_In_DateTime instanceof Date &&
      out.Started_DateTime   instanceof Date
    ) {
      const waitMs = out.Started_DateTime - out.Check_In_DateTime;
      out.Wait_Time_Minutes = waitMs / 60_000;
    }

    return out;
  });
}

// ---------------------------------------------------------------------------
// Step 5: Drop useless columns
// ---------------------------------------------------------------------------

const DROP_COLUMNS = new Set([
  'Mode', 'Location', 'Resource', 'Topic',
  'Check In At Date', 'Check In At Time',
  'Started At Date', 'Started At Time',
  'Ended At Date', 'Ended At Time',
  'Cancelled At Date', 'Cancelled At Time',
]);

/** @param {object[]} rows @returns {{ rows: object[], dropped: string[] }} */
export function dropUselessColumns(rows) {
  if (rows.length === 0) return { rows: [], dropped: [] };

  const dropped = Object.keys(rows[0]).filter(k => DROP_COLUMNS.has(k));
  const keep    = Object.keys(rows[0]).filter(k => !DROP_COLUMNS.has(k));

  const cleaned = rows.map(row => {
    const out = {};
    for (const k of keep) out[k] = row[k];
    return out;
  });

  return { rows: cleaned, dropped };
}

// ---------------------------------------------------------------------------
// Step 6: Validate data quality
// ---------------------------------------------------------------------------

/**
 * @param {object[]} rows
 * @returns {{ totalIssues: number, issues: string[], statusDistribution: object }}
 */
export function validateDataQuality(rows) {
  const issues = [];

  // Required fields
  for (const field of ['Unique ID', 'Status', 'Course']) {
    if (rows.length > 0 && !(field in rows[0])) {
      issues.push(`Missing required field: ${field}`);
    }
  }

  // Invalid status values
  const VALID_STATUSES = new Set(['Completed', 'Check In', 'Cancelled', 'In Progress']);
  const statusCounts = {};
  for (const row of rows) {
    const s = row.Status;
    if (s != null) statusCounts[s] = (statusCounts[s] ?? 0) + 1;
    if (s != null && !VALID_STATUSES.has(s)) {
      // Only count once per invalid value
    }
  }
  const invalidStatuses = rows.filter(r => r.Status != null && !VALID_STATUSES.has(r.Status));
  if (invalidStatuses.length) issues.push(`Invalid status values: ${invalidStatuses.length} records`);

  // Negative durations
  const negDur = rows.filter(r => {
    const v = r['Duration Minutes'];
    return v != null && Number(v) < 0;
  });
  if (negDur.length) issues.push(`Negative durations: ${negDur.length} records`);

  return { totalIssues: issues.length, issues, statusDistribution: statusCounts };
}

// ---------------------------------------------------------------------------
// Main cleaning pipeline
// ---------------------------------------------------------------------------

/**
 * Complete cleaning pipeline for walk-in (drop-in) sessions.
 * Mirrors walkin_cleaner.py:clean_walkin_data.
 *
 * @param {object[]} rows - raw rows from fileLoader (headers trimmed)
 * @returns {{ rows: object[], log: object }}
 */
export function cleanWalkinData(rows) {
  const log = { originalRows: rows.length, pipeline: 'walkin' };

  // Step 1: Parse datetimes
  let r = parseWalkinDatetimes(rows);

  // Step 2: Consolidate courses
  r = consolidateCourses(r);

  // Step 3: Duration outliers
  const { rows: noOutliers, stats: outlierStats } = handleDurationOutliers(r);
  r = noOutliers;
  log.outliersRemoved = outlierStats;

  // Step 4: Derived fields
  r = addDerivedFields(r);

  // Step 5: Drop useless columns
  const { rows: trimmed, dropped } = dropUselessColumns(r);
  r = trimmed;
  log.droppedColumns = dropped;

  // Step 6: Validate
  const quality = validateDataQuality(r);
  log.qualityReport = quality;
  log.finalRows = r.length;
  log.finalCols = r.length > 0 ? Object.keys(r[0]).length : 0;

  return { rows: r, log };
}
