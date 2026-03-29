/**
 * academicCalendar.test.js
 *
 * Tests for academicCalendar.js — semester detection and academic year labelling.
 * Parity: all rules match academic_calendar.py exactly.
 */

import { describe, it, expect } from 'vitest';
import {
  detectSemester,
  getAcademicYear,
  getSemesterLabel,
  addSemesterColumns,
  getSemesterOrder,
  filterBySemester,
  filterByAcademicYear,
} from '../src/core/academicCalendar.js';

// ---------------------------------------------------------------------------
// detectSemester
// ---------------------------------------------------------------------------

describe('detectSemester', () => {
  it('returns Spring for January (month 1)', () => {
    expect(detectSemester(new Date('2025-01-15'))).toBe('Spring');
  });
  it('returns Spring for May (month 5)', () => {
    expect(detectSemester(new Date('2025-05-31'))).toBe('Spring');
  });
  it('returns Summer for June (month 6)', () => {
    expect(detectSemester(new Date('2025-06-01'))).toBe('Summer');
  });
  it('returns Summer for August (month 8)', () => {
    expect(detectSemester(new Date('2025-08-15'))).toBe('Summer');
  });
  it('returns Fall for September (month 9)', () => {
    expect(detectSemester(new Date('2025-09-01'))).toBe('Fall');
  });
  it('returns Fall for December (month 12)', () => {
    expect(detectSemester(new Date('2025-12-31'))).toBe('Fall');
  });
  it('returns null for null input', () => {
    expect(detectSemester(null)).toBeNull();
  });
  it('returns null for invalid Date', () => {
    expect(detectSemester(new Date('invalid'))).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// getAcademicYear
// ---------------------------------------------------------------------------

describe('getAcademicYear', () => {
  it('Fall 2024 (Sep 2024) → 2024-2025', () => {
    expect(getAcademicYear(new Date('2024-09-01'))).toBe('2024-2025');
  });
  it('Spring 2025 (Mar 2025) → 2024-2025', () => {
    expect(getAcademicYear(new Date('2025-03-15'))).toBe('2024-2025');
  });
  it('Summer 2025 (Jul 2025) → 2024-2025', () => {
    expect(getAcademicYear(new Date('2025-07-01'))).toBe('2024-2025');
  });
  it('August 2025 (boundary month) → 2025-2026', () => {
    expect(getAcademicYear(new Date('2025-08-01'))).toBe('2025-2026');
  });
  it('Fall 2025 (Nov 2025) → 2025-2026', () => {
    expect(getAcademicYear(new Date('2025-11-01'))).toBe('2025-2026');
  });
  it('returns null for null input', () => {
    expect(getAcademicYear(null)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// getSemesterLabel
// ---------------------------------------------------------------------------

describe('getSemesterLabel', () => {
  it('Spring 2025 label', () => {
    expect(getSemesterLabel(new Date('2025-02-01'))).toBe('Spring 2025');
  });
  it('Summer 2024 label', () => {
    expect(getSemesterLabel(new Date('2024-07-15'))).toBe('Summer 2024');
  });
  it('Fall 2024 label', () => {
    expect(getSemesterLabel(new Date('2024-10-01'))).toBe('Fall 2024');
  });
  it('returns null for null input', () => {
    expect(getSemesterLabel(null)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// getSemesterOrder
// ---------------------------------------------------------------------------

describe('getSemesterOrder', () => {
  it('returns the canonical order ["Spring","Summer","Fall"]', () => {
    expect(getSemesterOrder()).toEqual(['Spring', 'Summer', 'Fall']);
  });
});

// ---------------------------------------------------------------------------
// addSemesterColumns
// ---------------------------------------------------------------------------

describe('addSemesterColumns', () => {
  const rows = [
    { Session_ID: 'A', Appointment_DateTime: new Date('2025-02-10') },
    { Session_ID: 'B', Appointment_DateTime: new Date('2024-10-05') },
    { Session_ID: 'C', Appointment_DateTime: new Date('2025-06-20') },
    { Session_ID: 'D', Appointment_DateTime: null },
  ];

  it('adds Semester column', () => {
    const result = addSemesterColumns(rows);
    expect(result[0].Semester).toBe('Spring');
    expect(result[1].Semester).toBe('Fall');
    expect(result[2].Semester).toBe('Summer');
  });

  it('adds Academic_Year column', () => {
    const result = addSemesterColumns(rows);
    expect(result[0].Academic_Year).toBe('2024-2025');
    expect(result[1].Academic_Year).toBe('2024-2025');
    expect(result[2].Academic_Year).toBe('2024-2025');
  });

  it('adds Semester_Label column', () => {
    const result = addSemesterColumns(rows);
    expect(result[0].Semester_Label).toBe('Spring 2025');
    expect(result[1].Semester_Label).toBe('Fall 2024');
  });

  it('handles null dates gracefully', () => {
    const result = addSemesterColumns(rows);
    expect(result[3].Semester).toBeNull();
    expect(result[3].Academic_Year).toBeNull();
  });

  it('accepts a custom dateColumn name', () => {
    const custom = [{ Check_In_DateTime: new Date('2025-09-15') }];
    const result = addSemesterColumns(custom, 'Check_In_DateTime');
    expect(result[0].Semester).toBe('Fall');
  });

  it('accepts date strings', () => {
    const strRows = [{ Appointment_DateTime: '2025-04-01T10:00:00' }];
    const result = addSemesterColumns(strRows);
    expect(result[0].Semester).toBe('Spring');
  });

  it('does not mutate input rows', () => {
    const original = rows.map(r => ({ ...r }));
    addSemesterColumns(rows);
    expect(rows[0].Semester).toBeUndefined();
    expect(rows[0].Session_ID).toBe(original[0].Session_ID);
  });
});

// ---------------------------------------------------------------------------
// filterBySemester
// ---------------------------------------------------------------------------

describe('filterBySemester', () => {
  const rows = [
    { id: 1, Appointment_DateTime: new Date('2025-02-01') }, // Spring
    { id: 2, Appointment_DateTime: new Date('2025-07-01') }, // Summer
    { id: 3, Appointment_DateTime: new Date('2025-10-01') }, // Fall
    { id: 4, Appointment_DateTime: new Date('2025-03-01') }, // Spring
  ];

  it('filters to Spring only', () => {
    const result = filterBySemester(rows, 'Spring');
    expect(result.map(r => r.id)).toEqual([1, 4]);
  });

  it('filters to multiple semesters', () => {
    const result = filterBySemester(rows, ['Spring', 'Fall']);
    expect(result.map(r => r.id)).toEqual([1, 3, 4]);
  });
});

// ---------------------------------------------------------------------------
// filterByAcademicYear
// ---------------------------------------------------------------------------

describe('filterByAcademicYear', () => {
  const rows = [
    { id: 1, Appointment_DateTime: new Date('2024-10-01') }, // AY 2024-2025
    { id: 2, Appointment_DateTime: new Date('2025-02-01') }, // AY 2024-2025
    { id: 3, Appointment_DateTime: new Date('2025-09-01') }, // AY 2025-2026
  ];

  it('filters to one academic year', () => {
    const result = filterByAcademicYear(rows, '2024-2025');
    expect(result.map(r => r.id)).toEqual([1, 2]);
  });

  it('filters to multiple academic years', () => {
    const result = filterByAcademicYear(rows, ['2024-2025', '2025-2026']);
    expect(result.map(r => r.id)).toEqual([1, 2, 3]);
  });
});
