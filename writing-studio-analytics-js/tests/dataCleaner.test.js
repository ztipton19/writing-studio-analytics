/**
 * dataCleaner.test.js
 *
 * Tests for the scheduled-session cleaning pipeline.
 * Phase 2 exit criterion: cleaning output matches Python on:
 *   - row count after outlier removal
 *   - which rows are dropped (by Session_ID)
 *   - IQR bounds for session lengths
 *   - column renames applied correctly
 */

import { describe, it, expect, beforeAll } from 'vitest';
import {
  recodeXXXX,
  mergeDateTimeColumns,
  renameColumns,
  convertTextRatingsToNumeric,
  removeUselessColumns,
  standardizeDataTypes,
  createCalculatedFields,
  simplifyLocation,
  removeSessionLengthOutliers,
  escapeExcelFormulas,
  validateDataQuality,
  cleanScheduledSessions,
} from '../src/core/dataCleaner.js';
import fixture from './fixtures/scheduled_rows.json';

const RAW = fixture.rows;
const OUTLIER_ID = fixture.outlier_row_id; // 'SCH004' — 10.0 hours

// ---------------------------------------------------------------------------
// recodeXXXX
// ---------------------------------------------------------------------------

describe('recodeXXXX', () => {
  it('replaces XXXX with N/A in Course column', () => {
    const rows = [{ Course: 'XXXX' }, { Course: 'ENGL1013' }];
    const out = recodeXXXX(rows);
    expect(out[0].Course).toBe('N/A');
    expect(out[1].Course).toBe('ENGL1013');
  });

  it('does not mutate input', () => {
    const rows = [{ Course: 'XXXX' }];
    recodeXXXX(rows);
    expect(rows[0].Course).toBe('XXXX');
  });
});

// ---------------------------------------------------------------------------
// mergeDateTimeColumns
// ---------------------------------------------------------------------------

describe('mergeDateTimeColumns', () => {
  it('creates Booking_DateTime from date+time pair', () => {
    const rows = [{
      'Requested At Date': '1/10/2025',
      'Requested At Time': '2:00 PM',
    }];
    const out = mergeDateTimeColumns(rows);
    expect(out[0].Booking_DateTime).toBeInstanceOf(Date);
    expect(out[0].Booking_DateTime.getFullYear()).toBe(2025);
    expect(out[0].Booking_DateTime.getMonth()).toBe(0); // January
  });

  it('creates Appointment_DateTime', () => {
    const rows = [{
      'Requested Start At Date': '1/15/2025',
      'Requested Start At Time': '10:00 AM',
    }];
    const out = mergeDateTimeColumns(rows);
    expect(out[0].Appointment_DateTime).toBeInstanceOf(Date);
  });

  it('returns null when date string is empty', () => {
    const rows = [{
      'Cancelled At Date': '',
      'Cancelled At Time': '',
    }];
    const out = mergeDateTimeColumns(rows);
    expect(out[0].Cancelled_DateTime).toBeNull();
  });

  it('preserves original date/time columns (they are removed in a later step)', () => {
    const rows = [{
      'Requested At Date': '1/10/2025',
      'Requested At Time': '2:00 PM',
    }];
    const out = mergeDateTimeColumns(rows);
    expect(out[0]['Requested At Date']).toBe('1/10/2025');
  });
});

// ---------------------------------------------------------------------------
// renameColumns
// ---------------------------------------------------------------------------

describe('renameColumns', () => {
  it('renames Unique ID → Session_ID', () => {
    const rows = [{ 'Unique ID': 'SCH001', Status: 'Attended' }];
    const { rows: out } = renameColumns(rows);
    expect(out[0].Session_ID).toBe('SCH001');
    expect(out[0]['Unique ID']).toBeUndefined();
  });

  it('renames Tutor Submitted Length → Actual_Session_Length', () => {
    const rows = [{ 'Tutor Submitted Length': '0.67' }];
    const { rows: out } = renameColumns(rows);
    expect(out[0].Actual_Session_Length).toBe('0.67');
  });

  it('renames Course → Document_Type', () => {
    const rows = [{ Course: 'ENGL1013' }];
    const { rows: out } = renameColumns(rows);
    expect(out[0].Document_Type).toBe('ENGL1013');
  });

  it('handles old Penji Overall_Satisfaction format', () => {
    const key = 'Student - On a scale of 1-7 (1="extremely dissatisfied," 7="extremely satisfied"), how satisfied are you with the help you received at the Writing Studio?';
    const rows = [{ [key]: '7' }];
    const { rows: out } = renameColumns(rows);
    expect(out[0].Overall_Satisfaction).toBe('7');
  });

  it('returns renamedCount matching actual renames', () => {
    const rows = [{ 'Unique ID': 'X', Status: 'Y', Unknown_Col: 'Z' }];
    const { renamedCount } = renameColumns(rows);
    expect(renamedCount).toBe(2); // Unique ID + Status
  });
});

// ---------------------------------------------------------------------------
// convertTextRatingsToNumeric
// ---------------------------------------------------------------------------

describe('convertTextRatingsToNumeric', () => {
  it('converts "It went very well" → 4', () => {
    const rows = [{ Tutor_Session_Rating: 'It went very well' }];
    const out = convertTextRatingsToNumeric(rows);
    expect(out[0].Tutor_Session_Rating).toBe(4);
  });

  it('converts "It went extremely well" → 5', () => {
    const rows = [{ Tutor_Session_Rating: 'It went extremely well' }];
    const out = convertTextRatingsToNumeric(rows);
    expect(out[0].Tutor_Session_Rating).toBe(5);
  });

  it('converts "It went moderately well" → 3', () => {
    const rows = [{ Tutor_Session_Rating: 'It went moderately well' }];
    const out = convertTextRatingsToNumeric(rows);
    expect(out[0].Tutor_Session_Rating).toBe(3);
  });

  it('extracts leading integer from "7 - Extremely satisfied"', () => {
    const rows = [{ Overall_Satisfaction: '7 - Extremely satisfied' }];
    const out = convertTextRatingsToNumeric(rows);
    expect(out[0].Overall_Satisfaction).toBe(7);
  });

  it('extracts leading integer from "5 - Extremely well"', () => {
    const rows = [{ Tutor_Rapport: '5 - Extremely well' }];
    const out = convertTextRatingsToNumeric(rows);
    expect(out[0].Tutor_Rapport).toBe(5);
  });

  it('returns null for empty/unknown rating text', () => {
    const rows = [{ Tutor_Session_Rating: '' }];
    const out = convertTextRatingsToNumeric(rows);
    expect(out[0].Tutor_Session_Rating).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// removeUselessColumns
// ---------------------------------------------------------------------------

describe('removeUselessColumns', () => {
  it('removes Appointment Type column', () => {
    const rows = [{ 'Appointment Type': '40min 1-on-1', Session_ID: 'X' }];
    const { rows: out, removedCols } = removeUselessColumns(rows);
    expect(out[0]['Appointment Type']).toBeUndefined();
    expect(removedCols).toContain('Appointment Type');
  });

  it('removes Requested Length column', () => {
    const rows = [{ 'Requested Length': '0.67', Session_ID: 'X' }];
    const { rows: out } = removeUselessColumns(rows);
    expect(out[0]['Requested Length']).toBeUndefined();
  });

  it('preserves columns not in the drop list', () => {
    const rows = [{ Session_ID: 'X', Status: 'Attended', Custom: 'value' }];
    const { rows: out } = removeUselessColumns(rows);
    expect(out[0].Session_ID).toBe('X');
    expect(out[0].Custom).toBe('value');
  });
});

// ---------------------------------------------------------------------------
// simplifyLocation
// ---------------------------------------------------------------------------

describe('simplifyLocation', () => {
  it('simplifies CORD location', () => {
    const rows = [{ Location: 'Writing Studio - CORD 209 (building located next to Old Main)' }];
    const out = simplifyLocation(rows);
    expect(out[0].Location).toBe('CORD');
  });

  it('simplifies Zoom location', () => {
    const rows = [{ Location: 'Zoom Meeting - Online' }];
    const out = simplifyLocation(rows);
    expect(out[0].Location).toBe('ZOOM');
  });

  it('preserves unknown locations as-is', () => {
    const rows = [{ Location: 'Library Room 101' }];
    const out = simplifyLocation(rows);
    expect(out[0].Location).toBe('Library Room 101');
  });

  it('handles missing Location column gracefully', () => {
    const rows = [{ Session_ID: 'X' }];
    expect(() => simplifyLocation(rows)).not.toThrow();
  });
});

// ---------------------------------------------------------------------------
// removeSessionLengthOutliers
// ---------------------------------------------------------------------------

describe('removeSessionLengthOutliers', () => {
  it('removes rows with extreme session length', () => {
    const rows = [
      { Session_ID: 'A', Actual_Session_Length: 0.67 },
      { Session_ID: 'B', Actual_Session_Length: 0.5  },
      { Session_ID: 'C', Actual_Session_Length: 0.75 },
      { Session_ID: 'D', Actual_Session_Length: 10.0 }, // outlier
    ];
    const { rows: out, stats } = removeSessionLengthOutliers(rows);
    expect(out.some(r => r.Session_ID === 'D')).toBe(false);
    expect(stats.removedCount).toBe(1);
  });

  it('keeps NaN session length rows', () => {
    const rows = [
      { Session_ID: 'A', Actual_Session_Length: 0.67 },
      { Session_ID: 'B', Actual_Session_Length: null },
    ];
    const { rows: out } = removeSessionLengthOutliers(rows);
    expect(out.some(r => r.Session_ID === 'B')).toBe(true);
  });

  it('uses lowerMin = 0.05 (3 min in hours)', () => {
    const rows = [
      { Session_ID: 'A', Actual_Session_Length: 0.67 },
      { Session_ID: 'B', Actual_Session_Length: 0.67 },
      { Session_ID: 'C', Actual_Session_Length: 0.67 },
      { Session_ID: 'D', Actual_Session_Length: 0.67 },
      { Session_ID: 'tiny', Actual_Session_Length: 0.01 }, // < 0.05
    ];
    const { rows: out } = removeSessionLengthOutliers(rows);
    // With only one distinct value and one outlier, IQR=0; lower = max(0.05, 0.67-0) = 0.67
    // The tiny row will be filtered
    expect(out.some(r => r.Session_ID === 'tiny')).toBe(false);
  });

  it('returns stats.lowerBound >= 0.05', () => {
    const rows = Array.from({ length: 10 }, (_, i) => ({
      Session_ID: `R${i}`, Actual_Session_Length: 0.5 + i * 0.05,
    }));
    const { stats } = removeSessionLengthOutliers(rows);
    expect(stats.lowerBound).toBeGreaterThanOrEqual(0.05);
  });
});

// ---------------------------------------------------------------------------
// escapeExcelFormulas
// ---------------------------------------------------------------------------

describe('escapeExcelFormulas', () => {
  it('prepends apostrophe to cells starting with -', () => {
    const rows = [{ note: '-some formula' }];
    const out = escapeExcelFormulas(rows);
    expect(out[0].note).toBe("'-some formula");
  });

  it('prepends apostrophe to cells starting with =', () => {
    const rows = [{ formula: '=SUM(A1)' }];
    const out = escapeExcelFormulas(rows);
    expect(out[0].formula).toBe("'=SUM(A1)");
  });

  it('leaves normal strings unchanged', () => {
    const rows = [{ note: 'Normal text' }];
    const out = escapeExcelFormulas(rows);
    expect(out[0].note).toBe('Normal text');
  });

  it('does not modify numeric or Date values', () => {
    const d = new Date('2025-01-01');
    const rows = [{ val: 42, date: d }];
    const out = escapeExcelFormulas(rows);
    expect(out[0].val).toBe(42);
    expect(out[0].date).toBe(d);
  });
});

// ---------------------------------------------------------------------------
// cleanScheduledSessions — full pipeline (fixture data)
// ---------------------------------------------------------------------------

describe('cleanScheduledSessions (fixture)', () => {
  let result;

  beforeAll(() => {
    result = cleanScheduledSessions(RAW, { removeOutliersFlag: true });
  });

  it('returns a rows array and log', () => {
    expect(Array.isArray(result.rows)).toBe(true);
    expect(result.log).toBeDefined();
  });

  it('removes the outlier row (SCH004, 10h session)', () => {
    const ids = result.rows.map(r => r.Session_ID);
    expect(ids).not.toContain(OUTLIER_ID);
  });

  it('keeps non-outlier rows', () => {
    const ids = result.rows.map(r => r.Session_ID);
    expect(ids).toContain('SCH001');
    expect(ids).toContain('SCH002');
    expect(ids).toContain('SCH005');
  });

  it('log.outliersRemoved.removedCount = 1', () => {
    expect(result.log.outliersRemoved.removedCount).toBe(1);
  });

  it('renames Unique ID → Session_ID', () => {
    expect(result.rows[0].Session_ID).toBeDefined();
    expect(result.rows[0]['Unique ID']).toBeUndefined();
  });

  it('recodes XXXX to N/A (SCH002)', () => {
    const sch002 = result.rows.find(r => r.Session_ID === 'SCH002');
    expect(sch002.Document_Type).toBe('N/A');
  });

  it('simplifies Location to CORD or ZOOM', () => {
    const locs = result.rows.map(r => r.Location).filter(Boolean);
    locs.forEach(l => expect(['CORD', 'ZOOM']).toContain(l));
  });

  it('converts text tutor ratings to numbers', () => {
    // SCH001 has "It went very well" → 4; SCH002/005 have "It went extremely well" → 5
    const sch001 = result.rows.find(r => r.Session_ID === 'SCH001');
    expect(sch001.Tutor_Session_Rating).toBe(4);
    const sch002 = result.rows.find(r => r.Session_ID === 'SCH002');
    expect(sch002.Tutor_Session_Rating).toBe(5);
  });

  it('creates Appointment_DateTime as Date object', () => {
    const sch001 = result.rows.find(r => r.Session_ID === 'SCH001');
    expect(sch001.Appointment_DateTime).toBeInstanceOf(Date);
  });

  it('adds Semester from Appointment_DateTime', () => {
    // SCH001: Jan 2025 → Spring; SCH003: Feb 2025 → Spring; SCH005: Mar 2025 → Spring
    const sch001 = result.rows.find(r => r.Session_ID === 'SCH001');
    expect(sch001.Semester).toBe('Spring');
  });

  it('computes Booking_Lead_Time_Hours', () => {
    const sch001 = result.rows.find(r => r.Session_ID === 'SCH001');
    expect(typeof sch001.Booking_Lead_Time_Hours).toBe('number');
    expect(sch001.Booking_Lead_Time_Hours).toBeGreaterThan(0);
  });

  it('creates Incentivized flag for SCH002 (Extra credit)', () => {
    const sch002 = result.rows.find(r => r.Session_ID === 'SCH002');
    expect(sch002.Extra_Credit).toBe(true);
    expect(sch002.Incentivized).toBe(true);
  });

  it('creates Incentivized flag for SCH005 (Class required)', () => {
    const sch005 = result.rows.find(r => r.Session_ID === 'SCH005');
    expect(sch005.Class_Required).toBe(true);
    expect(sch005.Incentivized).toBe(true);
  });

  it('does not include Appointment Type in output', () => {
    const keys = Object.keys(result.rows[0]);
    expect(keys).not.toContain('Appointment Type');
  });

  it('does not include Requested Length in output', () => {
    const keys = Object.keys(result.rows[0]);
    expect(keys).not.toContain('Requested Length');
  });

  it('log.originalRows matches fixture row count', () => {
    expect(result.log.originalRows).toBe(RAW.length);
  });

  it('log.finalRows = originalRows - 1 (one outlier removed)', () => {
    expect(result.log.finalRows).toBe(RAW.length - 1);
  });

  it('pipeline runs without outlier removal when flag is false', () => {
    const r2 = cleanScheduledSessions(RAW, { removeOutliersFlag: false });
    // All rows preserved (including outlier)
    expect(r2.rows.length).toBe(RAW.length);
  });
});
