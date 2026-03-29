/**
 * academicCalendar.js
 *
 * Semester detection and academic year labelling.
 * Direct port of src/utils/academic_calendar.py.
 *
 * Rules (matching Python exactly):
 *   Spring  = months 1–5  (Jan–May, inc. intersession)
 *   Summer  = months 6–8  (Jun–Aug, inc. intersession)
 *   Fall    = months 9–12 (Sep–Dec)
 *
 *   Academic year starts in Fall (Aug = month 8 is the boundary):
 *     month >= 8 → year / year+1   (e.g. Aug 2024 = "2024-2025")
 *     month <  8 → year-1 / year   (e.g. Mar 2025 = "2024-2025")
 *
 * All functions accept a JS Date object (or null/undefined → returns null).
 */

// ---------------------------------------------------------------------------
// Core helpers
// ---------------------------------------------------------------------------

/**
 * @param {Date|null|undefined} date
 * @returns {boolean}
 */
function isInvalid(date) {
  return date == null || !(date instanceof Date) || isNaN(date.getTime());
}

/**
 * Detect semester from a Date object.
 * Port of academic_calendar.py:detect_semester.
 *
 * @param {Date|null|undefined} date
 * @returns {'Spring'|'Summer'|'Fall'|null}
 */
export function detectSemester(date) {
  if (isInvalid(date)) return null;
  const m = date.getMonth() + 1; // 1-based month
  if (m >= 1 && m <= 5) return 'Spring';
  if (m >= 6 && m <= 8) return 'Summer';
  return 'Fall'; // 9–12
}

/**
 * Return academic year string like "2024-2025".
 * Port of academic_calendar.py:get_academic_year.
 *
 * @param {Date|null|undefined} date
 * @returns {string|null}
 */
export function getAcademicYear(date) {
  if (isInvalid(date)) return null;
  const y = date.getFullYear();
  const m = date.getMonth() + 1;
  if (m >= 8) return `${y}-${y + 1}`;
  return `${y - 1}-${y}`;
}

/**
 * Return full semester label like "Spring 2025".
 * Port of academic_calendar.py:get_semester_label.
 *
 * @param {Date|null|undefined} date
 * @returns {string|null}
 */
export function getSemesterLabel(date) {
  if (isInvalid(date)) return null;
  const semester = detectSemester(date);
  const year = date.getFullYear();
  return `${semester} ${year}`;
}

// ---------------------------------------------------------------------------
// Batch helpers
// ---------------------------------------------------------------------------

/**
 * Natural ordering for categorical sorts/charts.
 * @returns {string[]}
 */
export function getSemesterOrder() {
  return ['Spring', 'Summer', 'Fall'];
}

/**
 * Add Semester, Academic_Year, and Semester_Label fields to every row.
 * Port of academic_calendar.py:add_semester_columns.
 *
 * @param {object[]} rows
 * @param {string}   dateColumn - name of column that holds a JS Date (or date string)
 * @returns {object[]}
 */
export function addSemesterColumns(rows, dateColumn = 'Appointment_DateTime') {
  return rows.map(row => {
    let d = row[dateColumn];
    // Accept both Date objects and parseable strings
    if (typeof d === 'string' || typeof d === 'number') d = new Date(d);
    return {
      ...row,
      Semester: detectSemester(d),
      Academic_Year: getAcademicYear(d),
      Semester_Label: getSemesterLabel(d),
    };
  });
}

/**
 * Count sessions per semester label for a given date column.
 * Port of academic_calendar.py:get_semester_stats.
 *
 * @param {object[]} rows
 * @param {string}   dateColumn
 * @returns {Object<string, number>}
 */
export function getSemesterStats(rows, dateColumn = 'Appointment_DateTime') {
  const counts = {};
  for (const row of rows) {
    let d = row[dateColumn];
    if (typeof d === 'string' || typeof d === 'number') d = new Date(d);
    const label = getSemesterLabel(d);
    if (label != null) counts[label] = (counts[label] ?? 0) + 1;
  }
  return counts;
}

// ---------------------------------------------------------------------------
// Filter helpers
// ---------------------------------------------------------------------------

/**
 * Filter rows to only those whose date column falls in the given semester(s).
 * Port of academic_calendar.py:filter_by_semester.
 *
 * @param {object[]}        rows
 * @param {string|string[]} semester  e.g. 'Spring' or ['Spring','Fall']
 * @param {string}          dateColumn
 * @returns {object[]}
 */
export function filterBySemester(rows, semester, dateColumn = 'Appointment_DateTime') {
  const allowed = new Set(Array.isArray(semester) ? semester : [semester]);
  return rows.filter(row => {
    let d = row[dateColumn];
    if (typeof d === 'string' || typeof d === 'number') d = new Date(d);
    return allowed.has(detectSemester(d));
  });
}

/**
 * Filter rows to only those in the given academic year(s).
 * Port of academic_calendar.py:filter_by_academic_year.
 *
 * @param {object[]}        rows
 * @param {string|string[]} academicYear  e.g. '2024-2025'
 * @param {string}          dateColumn
 * @returns {object[]}
 */
export function filterByAcademicYear(rows, academicYear, dateColumn = 'Appointment_DateTime') {
  const allowed = new Set(Array.isArray(academicYear) ? academicYear : [academicYear]);
  return rows.filter(row => {
    let d = row[dateColumn];
    if (typeof d === 'string' || typeof d === 'number') d = new Date(d);
    return allowed.has(getAcademicYear(d));
  });
}
