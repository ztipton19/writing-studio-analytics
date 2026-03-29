/**
 * dataCleaner.js
 *
 * Cleaning pipeline for scheduled 40-minute sessions.
 * Function-for-function port of src/core/data_cleaner.py.
 *
 * Input:  raw rows[] from fileLoader (column names already trimmed by Phase 1)
 * Output: { rows, log }
 *
 * Public API:
 *   cleanScheduledSessions(rows, { removeOutliersFlag })  → { rows, log }
 *   detectSessionType(headers)   — re-exported from fileLoader
 */

import { iqrOutlierBounds } from '../stats/statistics.js';
import { detectSemester, getAcademicYear, getSemesterLabel } from './academicCalendar.js';

// ---------------------------------------------------------------------------
// Step 0: Recode XXXX → N/A in Course column
// ---------------------------------------------------------------------------

/** @param {object[]} rows @returns {object[]} */
export function recodeXXXX(rows) {
  return rows.map(row => {
    if (row['Course'] === 'XXXX') return { ...row, Course: 'N/A' };
    return row;
  });
}

// ---------------------------------------------------------------------------
// Step 1: Merge date + time strings into ISO datetime strings
// ---------------------------------------------------------------------------

/**
 * Pairs of (dateCol, timeCol, newCol) — matches data_cleaner.py:merge_datetime_columns.
 */
const DATETIME_PAIRS = [
  ['Requested At Date',       'Requested At Time',       'Booking_DateTime'],
  ['Requested Start At Date', 'Requested Start At Time', 'Appointment_DateTime'],
  ['Started At Date',         'Started At Time',         'Actual_Start_DateTime'],
  ['Ended At Date',           'Ended At Time',           'Actual_End_DateTime'],
  ['Cancelled At Date',       'Cancelled At Time',       'Cancelled_DateTime'],
];

/**
 * Parse "M/D/YYYY h:mm AM/PM" or ISO strings into JS Date objects.
 * Returns null when either date or time is blank/invalid.
 *
 * @param {string} dateStr
 * @param {string} timeStr
 * @returns {Date|null}
 */
function parseDateTimeStr(dateStr, timeStr) {
  if (!dateStr || !timeStr) return null;
  const combined = `${String(dateStr).trim()} ${String(timeStr).trim()}`;
  const d = new Date(combined);
  return isNaN(d.getTime()) ? null : d;
}

/** @param {object[]} rows @returns {object[]} */
export function mergeDateTimeColumns(rows) {
  return rows.map(row => {
    const extra = {};
    for (const [datCol, timCol, newCol] of DATETIME_PAIRS) {
      if (datCol in row && timCol in row) {
        extra[newCol] = parseDateTimeStr(row[datCol], row[timCol]);
      }
    }
    return { ...row, ...extra };
  });
}

// ---------------------------------------------------------------------------
// Step 2: Rename columns to analysis-friendly names
// ---------------------------------------------------------------------------

/**
 * Mirrors data_cleaner.py:rename_columns rename_map (both old and new Penji formats).
 */
const RENAME_MAP = {
  'Unique ID':            'Session_ID',
  'Status':               'Status',
  'Course':               'Document_Type',
  'Location':             'Location',
  'Tutor Submitted Length': 'Actual_Session_Length',
  'Student Attendance':   'Attendance_Status',
  'Session Feedback From Student': 'Student_Feedback',

  // Pre-session (Agenda)
  'Agenda - How confident do you feel about your writing assignment right now? (1="Not at all"; 5="Very")': 'Pre_Confidence',
  'Agenda - Is this your first appointment?': 'Is_First_Appointment',
  'Agenda - Please check one of the following boxes to help us determine the context of your visit.': 'Visit_Context',
  'Agenda - Roughly speaking, what stage of the writing process are you in right now?': 'Writing_Stage',
  'Agenda - What would you like to focus on during this appointment?': 'Focus_Area',
  'Agenda - When is your paper due?': 'Paper_Due_Date',

  // Post-session (new Penji format)
  'Student - How confident do you feel about your writing assignment now that your meeting is over (1="Not at all"; 5="Very")?': 'Post_Confidence',
  'Student - How satisfied are you with the help you received at the Writing Studio (1="extremely dissatisfied," 7="extremely satisfied")?': 'Overall_Satisfaction',

  // Post-session (old Penji format — backward compat)
  'Student - How confident do you feel about your writing assignment now that your meeting is over? (1="Not at all"; 5="Very")': 'Post_Confidence',
  'Student - On a scale of 1-7 (1="extremely dissatisfied," 7="extremely satisfied"), how satisfied are you with the help you received at the Writing Studio?': 'Overall_Satisfaction',

  // Common formats
  'Student - On a scale of 1-5 (1="not at all," 5="extremely well"), how well did you get along with your tutor?': 'Tutor_Rapport',
  'Student - On a scale of 1-5 (1="not easy at all", 5="extremely easy"), how easy was it to use our website and scheduling software to schedule and attend your appointment?': 'Platform_Ease',
  'Student - On a scale of 1-5 (1="very poorly", 5="very well"), how well would you say your your appointment went?': 'Session_Quality',
  'Student - On a scale of 1-5 (1="very poorly", 5="very well"), how well would you say your appointment went?': 'Session_Quality',
  "Student - Were you offered any of the following incentives for today's visit? Please select any that apply.": 'Incentives_Offered',
  'Tutor - Overall, how well would you say that the consultation went?': 'Tutor_Session_Rating',
};

/**
 * Rename columns in each row according to RENAME_MAP.
 * Keys not in the map pass through unchanged.
 *
 * @param {object[]} rows
 * @returns {{ rows: object[], renamedCount: number }}
 */
export function renameColumns(rows) {
  if (rows.length === 0) return { rows: [], renamedCount: 0 };

  const firstRow = rows[0];
  const renamedCount = Object.keys(firstRow).filter(k => RENAME_MAP[k] !== undefined).length;

  const renamed = rows.map(row => {
    const out = {};
    for (const [k, v] of Object.entries(row)) {
      out[RENAME_MAP[k] ?? k] = v;
    }
    return out;
  });

  return { rows: renamed, renamedCount };
}

// ---------------------------------------------------------------------------
// Step 2.5: Convert text ratings to numeric
// ---------------------------------------------------------------------------

const TUTOR_RATING_MAP = {
  'It went extremely well': 5,
  'It went very well':      4,
  'It went moderately well': 3,
  'It went somewhat well':  2,
  "It didn't go well at all": 1,
};

const NUMERIC_PREFIX_FIELDS = [
  'Tutor_Rapport', 'Platform_Ease', 'Session_Quality', 'Overall_Satisfaction',
];

/** @param {object[]} rows @returns {object[]} */
export function convertTextRatingsToNumeric(rows) {
  return rows.map(row => {
    const out = { ...row };

    if ('Tutor_Session_Rating' in out) {
      const v = out['Tutor_Session_Rating'];
      const mapped = TUTOR_RATING_MAP[v] ?? TUTOR_RATING_MAP[String(v).toLowerCase()];
      out['Tutor_Session_Rating'] = mapped ?? null;
    }

    for (const field of NUMERIC_PREFIX_FIELDS) {
      if (field in out) {
        const raw = String(out[field] ?? '').trim();
        const match = raw.match(/^(\d+)/);
        out[field] = match ? Number(match[1]) : null;
      }
    }

    return out;
  });
}

// ---------------------------------------------------------------------------
// Step 3: Remove useless columns
// ---------------------------------------------------------------------------

const USELESS_COLUMNS = new Set([
  'Appointment Type', 'Kind', 'Session_Kind',
  'Agenda - For which course are you writing this document? (If not applicable, write "N/A")',
  'Course_Subject',
  'Requested At Date', 'Requested At Time',
  'Requested Start At Date', 'Requested Start At Time',
  'Requested End At Date', 'Requested End At Time',
  'Scheduled Start At Date', 'Scheduled Start At Time',
  'Scheduled End At Date', 'Scheduled End At Time',
  'Started At Date', 'Started At Time',
  'Ended At Date', 'Ended At Time',
  'Cancelled At Date', 'Cancelled At Time',
  'Requested Length',
  'Source Kind', 'Booking Flow', 'Booking_Source', 'Booking_Method',
  'Student Attendance Reason', 'Attendance_Reason',
  'Recurrence', 'Section',
  'Session Feedback From Tutor',
  'Agenda - If you are meeting a Writing Consultant in-person, would you like to meet in a sensory-friendly, Low Distraction Room (LDR) if it is available?',
  'Agenda - If you have access to any rubrics or assignment sheets, please attach them here.',
  'Agenda - Please attach any assignment sheets, written directions, or rubrics for your paper.',
  'Agenda - Please upload your paper here.',
  'Tutor - Was this a mock or test consultation?',
  'Tutor - Please provide a brief overview of the topics discussed or issues addressed during your consultation.',
  "Agenda - Is there anything else you'd like to share?",
  'Cancel Reason',
  'Student - Please share any comments that you\'d like your tutor to see.',
  'Student - Please share any obstacles, disappointments, or problems that you encountered during your consultation at the Writing Studio.',
]);

/** @param {object[]} rows @returns {{ rows: object[], removedCols: string[] }} */
export function removeUselessColumns(rows) {
  if (rows.length === 0) return { rows: [], removedCols: [] };

  const removedCols = Object.keys(rows[0]).filter(k => USELESS_COLUMNS.has(k));
  const keep = Object.keys(rows[0]).filter(k => !USELESS_COLUMNS.has(k));

  const cleaned = rows.map(row => {
    const out = {};
    for (const k of keep) out[k] = row[k];
    return out;
  });

  return { rows: cleaned, removedCols };
}

// ---------------------------------------------------------------------------
// Step 4: Standardize data types (parse numerics, nullify empty strings)
// ---------------------------------------------------------------------------

const NUMERIC_COLS = new Set([
  'Actual_Session_Length', 'Pre_Confidence', 'Post_Confidence',
  'Tutor_Rapport', 'Platform_Ease', 'Session_Quality',
  'Overall_Satisfaction', 'Tutor_Session_Rating',
]);

/** @param {object[]} rows @returns {object[]} */
export function standardizeDataTypes(rows) {
  return rows.map(row => {
    const out = { ...row };
    for (const col of NUMERIC_COLS) {
      if (col in out) {
        const raw = out[col];
        // Treat empty string and null/undefined as missing (null), not zero
        if (raw == null || raw === '') {
          out[col] = null;
        } else {
          const n = Number(raw);
          out[col] = isNaN(n) ? null : n;
        }
      }
    }
    return out;
  });
}

// ---------------------------------------------------------------------------
// Step 5: Create calculated fields
// ---------------------------------------------------------------------------

/** @param {object[]} rows @returns {object[]} */
export function createCalculatedFields(rows) {
  return rows.map(row => {
    const out = { ...row };

    // Booking lead time
    if (out.Booking_DateTime instanceof Date && out.Appointment_DateTime instanceof Date) {
      const diffHours =
        (out.Appointment_DateTime - out.Booking_DateTime) / 3_600_000;
      out.Booking_Lead_Time_Hours = diffHours;
      out.Booking_Lead_Time_Days  = diffHours / 24;
    }

    // Confidence change
    if (out.Pre_Confidence != null && out.Post_Confidence != null) {
      out.Confidence_Change = out.Post_Confidence - out.Pre_Confidence;
    }

    // Actual session duration from timestamps
    if (
      out.Actual_Start_DateTime instanceof Date &&
      out.Actual_End_DateTime instanceof Date
    ) {
      out.Calculated_Session_Length =
        (out.Actual_End_DateTime - out.Actual_Start_DateTime) / 3_600_000;
    }

    // First-timer flag
    if (out.Is_First_Appointment != null) {
      const v = String(out.Is_First_Appointment).toLowerCase().trim();
      out.Is_First_Timer = v === 'yes' || v === 'y' || v === 'true';
    }

    // Academic calendar (from Appointment_DateTime)
    if (out.Appointment_DateTime instanceof Date) {
      const d = out.Appointment_DateTime;
      out.Semester       = detectSemester(d);
      out.Academic_Year  = getAcademicYear(d);
      out.Semester_Label = getSemesterLabel(d);
    }

    // Incentive boolean flags
    if (out.Incentives_Offered != null) {
      const s = String(out.Incentives_Offered).toLowerCase();
      out.Extra_Credit  = s.includes('extra credit');
      out.Class_Required = s.includes('entire class was required');
      out.Incentivized   = out.Extra_Credit || out.Class_Required;
    }

    return out;
  });
}

// ---------------------------------------------------------------------------
// Step 5.5: Simplify location names
// ---------------------------------------------------------------------------

/** @param {object[]} rows @returns {object[]} */
export function simplifyLocation(rows) {
  return rows.map(row => {
    if (!('Location' in row) || row.Location == null) return row;
    const s = String(row.Location).toLowerCase();
    let loc;
    if (s.includes('cord') || s.includes('old main')) loc = 'CORD';
    else if (s.includes('zoom') || s.includes('online')) loc = 'ZOOM';
    else loc = row.Location;
    return { ...row, Location: loc };
  });
}

// ---------------------------------------------------------------------------
// Step 6: Remove outliers on Actual_Session_Length (hours, lowerMin = 0.05)
// ---------------------------------------------------------------------------

const SCHEDULED_LOWER_MIN = 0.05; // 3 minutes in hours

/**
 * Remove IQR outliers from the Actual_Session_Length column.
 *
 * @param {object[]} rows
 * @returns {{ rows: object[], stats: object }}
 */
export function removeSessionLengthOutliers(rows) {
  const colName = 'Actual_Session_Length';
  const original = rows.length;

  const values = rows
    .map(r => r[colName])
    .filter(v => v != null && !isNaN(Number(v)))
    .map(Number);

  if (values.length === 0) {
    return { rows, stats: { removedCount: 0, method: 'no_data' } };
  }

  const { lower, upper } = iqrOutlierBounds(values, SCHEDULED_LOWER_MIN);

  const cleaned = rows.filter(row => {
    const v = row[colName];
    if (v == null || isNaN(Number(v))) return true; // keep NaN rows
    return Number(v) >= lower && Number(v) <= upper;
  });

  const removedCount = original - cleaned.length;
  return {
    rows: cleaned,
    stats: {
      removedCount,
      removedPct: original > 0 ? (removedCount / original) * 100 : 0,
      lowerBound: Math.round(lower * 1e6) / 1e6,
      upperBound: Math.round(upper * 1e6) / 1e6,
      method: 'iqr',
      originalCount: original,
      finalCount: cleaned.length,
    },
  };
}

// ---------------------------------------------------------------------------
// Step 7: Escape Excel formula characters
// ---------------------------------------------------------------------------

/** @param {object[]} rows @returns {object[]} */
export function escapeExcelFormulas(rows) {
  return rows.map(row => {
    const out = {};
    for (const [k, v] of Object.entries(row)) {
      if (typeof v === 'string' && v.length > 0 && (v[0] === '-' || v[0] === '=')) {
        out[k] = `'${v}`;
      } else {
        out[k] = v;
      }
    }
    return out;
  });
}

// ---------------------------------------------------------------------------
// Step 8: Validate data quality
// ---------------------------------------------------------------------------

/**
 * @param {object[]} rows
 * @returns {{ issues: string[], warnings: string[] }}
 */
export function validateDataQuality(rows) {
  const issues = [];
  const warnings = [];

  // Session length range check
  const lengths = rows
    .map(r => r.Actual_Session_Length)
    .filter(v => v != null && !isNaN(Number(v)))
    .map(Number);

  const tooLong  = lengths.filter(v => v > 3);
  const tooShort = lengths.filter(v => v < 0.05);
  if (tooLong.length)  issues.push(`${tooLong.length} sessions longer than 3 hours`);
  if (tooShort.length) issues.push(`${tooShort.length} sessions shorter than 3 minutes`);

  // Score range checks
  const scoreChecks = [
    ['Pre_Confidence', 1, 5], ['Post_Confidence', 1, 5],
    ['Tutor_Rapport', 1, 5], ['Platform_Ease', 1, 5],
    ['Session_Quality', 1, 5], ['Overall_Satisfaction', 1, 7],
    ['Tutor_Session_Rating', 1, 5],
  ];
  for (const [col, min, max] of scoreChecks) {
    const vals = rows
      .map(r => r[col])
      .filter(v => v != null && !isNaN(Number(v)))
      .map(Number);
    const invalid = vals.filter(v => v < min || v > max);
    if (invalid.length) {
      issues.push(`${invalid.length} ${col} scores outside ${min}–${max}`);
    }
  }

  // Future appointments
  const now = Date.now();
  const future = rows.filter(
    r => r.Appointment_DateTime instanceof Date && r.Appointment_DateTime.getTime() > now
  );
  if (future.length) {
    warnings.push(`${future.length} future appointments (likely scheduled sessions)`);
  }

  return { issues, warnings };
}

// ---------------------------------------------------------------------------
// Main cleaning pipeline: scheduled sessions
// ---------------------------------------------------------------------------

/**
 * Complete cleaning pipeline for scheduled 40-minute sessions.
 * Mirrors data_cleaner.py:clean_scheduled_sessions.
 *
 * @param {object[]} rows - raw rows (already header-trimmed by Phase 1)
 * @param {{ removeOutliersFlag?: boolean }} [opts]
 * @returns {{ rows: object[], log: object }}
 */
export function cleanScheduledSessions(rows, { removeOutliersFlag = true } = {}) {
  const log = {
    originalRows: rows.length,
    pipeline: 'scheduled',
  };

  // Step 0: Recode XXXX → N/A
  let r = recodeXXXX(rows);

  // Step 1: Merge date/time pairs into Date objects
  r = mergeDateTimeColumns(r);

  // Step 2: Rename columns
  const { rows: renamed, renamedCount } = renameColumns(r);
  r = renamed;
  log.renamedColumns = renamedCount;

  // Step 2.5: Convert text ratings to numeric
  r = convertTextRatingsToNumeric(r);

  // Step 3: Remove useless columns
  const { rows: trimmed, removedCols } = removeUselessColumns(r);
  r = trimmed;
  log.removedColumns = removedCols;

  // Step 4: Standardize data types
  r = standardizeDataTypes(r);

  // Step 5: Create calculated fields
  r = createCalculatedFields(r);

  // Step 5.5: Simplify location
  r = simplifyLocation(r);

  // Step 6: Outlier removal (optional)
  if (removeOutliersFlag) {
    const { rows: noOutliers, stats } = removeSessionLengthOutliers(r);
    r = noOutliers;
    log.outliersRemoved = stats;
  }

  // Step 7: Escape Excel formulas
  r = escapeExcelFormulas(r);

  // Step 8: Validate
  const { issues, warnings } = validateDataQuality(r);
  log.qualityIssues   = issues;
  log.qualityWarnings = warnings;
  log.finalRows       = r.length;
  log.finalCols       = r.length > 0 ? Object.keys(r[0]).length : 0;

  return { rows: r, log };
}
