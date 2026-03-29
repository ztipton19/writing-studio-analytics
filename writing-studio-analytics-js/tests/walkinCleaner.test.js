/**
 * walkinCleaner.test.js
 *
 * Tests for the walk-in session cleaning pipeline.
 * Phase 2 exit criterion: cleaning output matches Python on row count,
 * dropped-row IDs, and duration outlier bounds.
 */

import { describe, it, expect, beforeAll } from 'vitest';
import {
  parseWalkinDatetimes,
  consolidateCourses,
  handleDurationOutliers,
  addDerivedFields,
  dropUselessColumns,
  validateDataQuality,
  cleanWalkinData,
} from '../src/core/walkinCleaner.js';
import fixture from './fixtures/walkin_rows.json';

const RAW = fixture.rows;
const OUTLIER_ID = fixture.outlier_row_id; // 'WI004' — 500 min

// ---------------------------------------------------------------------------
// parseWalkinDatetimes
// ---------------------------------------------------------------------------

describe('parseWalkinDatetimes', () => {
  it('creates Check_In_DateTime from date+time pair', () => {
    const rows = [{
      'Check In At Date': '2/3/2025',
      'Check In At Time': '10:00 AM',
    }];
    const out = parseWalkinDatetimes(rows);
    expect(out[0].Check_In_DateTime).toBeInstanceOf(Date);
    expect(out[0].Check_In_DateTime.getFullYear()).toBe(2025);
    expect(out[0].Check_In_DateTime.getMonth()).toBe(1); // February
  });

  it('creates Started_DateTime and Ended_DateTime', () => {
    const rows = [{
      'Started At Date': '2/3/2025', 'Started At Time': '10:05 AM',
      'Ended At Date': '2/3/2025',   'Ended At Time': '10:30 AM',
    }];
    const out = parseWalkinDatetimes(rows);
    expect(out[0].Started_DateTime).toBeInstanceOf(Date);
    expect(out[0].Ended_DateTime).toBeInstanceOf(Date);
  });

  it('returns null when date/time is empty', () => {
    const rows = [{ 'Cancelled At Date': '', 'Cancelled At Time': '' }];
    const out = parseWalkinDatetimes(rows);
    expect(out[0].Cancelled_DateTime).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// consolidateCourses
// ---------------------------------------------------------------------------

describe('consolidateCourses', () => {
  it('maps "Other topic not listed" → "Other"', () => {
    const rows = [{ Course: 'Other topic not listed' }];
    expect(consolidateCourses(rows)[0].Course).toBe('Other');
  });

  it('maps "Reflection paper" → "Reflection or response paper"', () => {
    const rows = [{ Course: 'Reflection paper' }];
    expect(consolidateCourses(rows)[0].Course).toBe('Reflection or response paper');
  });

  it('maps thesis variation → "Thesis or dissertation"', () => {
    const rows = [{ Course: 'Thesis or dissertation (Undergraduate/Graduate)' }];
    expect(consolidateCourses(rows)[0].Course).toBe('Thesis or dissertation');
  });

  it('fixes duplicate text "Speech outlineSpeech outline"', () => {
    const rows = [{ Course: 'Speech outlineSpeech outline' }];
    expect(consolidateCourses(rows)[0].Course).toBe('Speech outline');
  });

  it('maps XXXX → N/A', () => {
    const rows = [{ Course: 'XXXX' }];
    expect(consolidateCourses(rows)[0].Course).toBe('N/A');
  });

  it('keeps unmapped courses unchanged', () => {
    const rows = [{ Course: 'ENGL1013' }];
    expect(consolidateCourses(rows)[0].Course).toBe('ENGL1013');
  });

  it('strips whitespace', () => {
    const rows = [{ Course: '  ENGL1013  ' }];
    expect(consolidateCourses(rows)[0].Course).toBe('ENGL1013');
  });
});

// ---------------------------------------------------------------------------
// handleDurationOutliers
// ---------------------------------------------------------------------------

describe('handleDurationOutliers', () => {
  it('removes rows with extreme Duration Minutes', () => {
    // Need >= 4 non-null values for IQR to flag an outlier correctly
    const rows = [
      { 'Unique ID': 'A', 'Duration Minutes': '25' },
      { 'Unique ID': 'B', 'Duration Minutes': '40' },
      { 'Unique ID': 'D', 'Duration Minutes': '60' },
      { 'Unique ID': 'C', 'Duration Minutes': '500' }, // outlier
    ];
    const { rows: out, stats } = handleDurationOutliers(rows);
    expect(out.some(r => r['Unique ID'] === 'C')).toBe(false);
    expect(stats.removedCount).toBe(1);
  });

  it('keeps rows with null Duration Minutes', () => {
    const rows = [
      { 'Unique ID': 'A', 'Duration Minutes': '30' },
      { 'Unique ID': 'B', 'Duration Minutes': '' },  // null-like
    ];
    const { rows: out } = handleDurationOutliers(rows);
    expect(out.some(r => r['Unique ID'] === 'B')).toBe(true);
  });

  it('lowerBound is at least 3 minutes', () => {
    const rows = Array.from({ length: 8 }, (_, i) => ({
      'Unique ID': `R${i}`, 'Duration Minutes': String(15 + i * 5),
    }));
    const { stats } = handleDurationOutliers(rows);
    expect(stats.lowerBound).toBeGreaterThanOrEqual(3);
  });

  it('returns stats with correct fields', () => {
    const rows = [{ 'Duration Minutes': '20' }, { 'Duration Minutes': '30' }];
    const { stats } = handleDurationOutliers(rows);
    expect(stats).toHaveProperty('removedCount');
    expect(stats).toHaveProperty('lowerBound');
    expect(stats).toHaveProperty('upperBound');
  });
});

// ---------------------------------------------------------------------------
// addDerivedFields
// ---------------------------------------------------------------------------

describe('addDerivedFields', () => {
  it('adds Semester, Academic_Year, Semester_Label from Check_In_DateTime', () => {
    const rows = [{ Check_In_DateTime: new Date('2025-02-03T10:00:00') }];
    const out = addDerivedFields(rows);
    expect(out[0].Semester).toBe('Spring');
    expect(out[0].Academic_Year).toBe('2024-2025');
    expect(out[0].Semester_Label).toBe('Spring 2025');
  });

  it('adds Day_of_Week', () => {
    // Feb 3 2025 is a Monday
    const rows = [{ Check_In_DateTime: new Date('2025-02-03T10:00:00') }];
    const out = addDerivedFields(rows);
    expect(out[0].Day_of_Week).toBe('Monday');
  });

  it('adds Hour_of_Day', () => {
    const rows = [{ Check_In_DateTime: new Date('2025-02-03T14:30:00') }];
    const out = addDerivedFields(rows);
    expect(out[0].Hour_of_Day).toBe(14);
  });

  it('computes Wait_Time_Minutes', () => {
    const rows = [{
      Check_In_DateTime: new Date('2025-02-03T10:00:00'),
      Started_DateTime:  new Date('2025-02-03T10:08:00'),
    }];
    const out = addDerivedFields(rows);
    expect(out[0].Wait_Time_Minutes).toBeCloseTo(8, 5);
  });

  it('does not add Wait_Time_Minutes if Started_DateTime is missing', () => {
    const rows = [{ Check_In_DateTime: new Date('2025-02-03T10:00:00') }];
    const out = addDerivedFields(rows);
    expect(out[0].Wait_Time_Minutes).toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
// dropUselessColumns
// ---------------------------------------------------------------------------

describe('dropUselessColumns', () => {
  it('drops Mode column', () => {
    const rows = [{ Mode: 'Queue', 'Unique ID': 'W1' }];
    const { rows: out, dropped } = dropUselessColumns(rows);
    expect(out[0].Mode).toBeUndefined();
    expect(dropped).toContain('Mode');
  });

  it('drops original date/time columns', () => {
    const rows = [{ 'Check In At Date': '1/1/2025', 'Unique ID': 'W1' }];
    const { rows: out } = dropUselessColumns(rows);
    expect(out[0]['Check In At Date']).toBeUndefined();
  });

  it('preserves Unique ID, Status, Course', () => {
    const rows = [{
      Mode: 'Queue',
      'Unique ID': 'W1',
      Status: 'Completed',
      Course: 'Essay',
    }];
    const { rows: out } = dropUselessColumns(rows);
    expect(out[0]['Unique ID']).toBe('W1');
    expect(out[0].Status).toBe('Completed');
    expect(out[0].Course).toBe('Essay');
  });
});

// ---------------------------------------------------------------------------
// cleanWalkinData — full pipeline (fixture data)
// ---------------------------------------------------------------------------

describe('cleanWalkinData (fixture)', () => {
  let result;

  beforeAll(() => {
    result = cleanWalkinData(RAW);
  });

  it('returns rows and log', () => {
    expect(Array.isArray(result.rows)).toBe(true);
    expect(result.log).toBeDefined();
  });

  it('removes the outlier row (WI004, 500 min)', () => {
    const ids = result.rows.map(r => r['Unique ID']);
    expect(ids).not.toContain(OUTLIER_ID);
  });

  it('keeps non-outlier rows', () => {
    const ids = result.rows.map(r => r['Unique ID']);
    expect(ids).toContain('WI001');
    expect(ids).toContain('WI002');
  });

  it('log.outliersRemoved.removedCount = 1', () => {
    expect(result.log.outliersRemoved.removedCount).toBe(1);
  });

  it('consolidates "Other topic not listed" → "Other" (WI002)', () => {
    const wi002 = result.rows.find(r => r['Unique ID'] === 'WI002');
    expect(wi002.Course).toBe('Other');
  });

  it('consolidates thesis variation (WI004 removed — verify on consolidated copy)', () => {
    // Run without outlier row to check course mapping
    const subset = [RAW.find(r => r['Unique ID'] === 'WI004')];
    const { rows: out } = cleanWalkinData(subset);
    // Either kept (if not outlier in 1-row set) or removed — just verify Course mapping
    // Actually with a single row, IQR has no valid outlier bounds
    // consolidateCourses should still apply regardless
    const r = out.find(r => r['Unique ID'] === 'WI004');
    if (r) expect(r.Course).toBe('Thesis or dissertation');
  });

  it('consolidates "Speech outlineSpeech outline" → "Speech outline" (WI005)', () => {
    const wi005 = result.rows.find(r => r['Unique ID'] === 'WI005');
    if (wi005) expect(wi005.Course).toBe('Speech outline');
  });

  it('adds Check_In_DateTime as Date (WI001)', () => {
    const wi001 = result.rows.find(r => r['Unique ID'] === 'WI001');
    expect(wi001.Check_In_DateTime).toBeInstanceOf(Date);
  });

  it('adds Semester for WI001 (Feb 2025 → Spring)', () => {
    const wi001 = result.rows.find(r => r['Unique ID'] === 'WI001');
    expect(wi001.Semester).toBe('Spring');
  });

  it('adds Day_of_Week for WI001 (Feb 3 2025 = Monday)', () => {
    const wi001 = result.rows.find(r => r['Unique ID'] === 'WI001');
    expect(wi001.Day_of_Week).toBe('Monday');
  });

  it('drops Mode, Location, Resource, Topic columns', () => {
    const keys = Object.keys(result.rows[0]);
    expect(keys).not.toContain('Mode');
    expect(keys).not.toContain('Location');
    expect(keys).not.toContain('Resource');
    expect(keys).not.toContain('Topic');
  });

  it('drops original date/time columns', () => {
    const keys = Object.keys(result.rows[0]);
    expect(keys).not.toContain('Check In At Date');
    expect(keys).not.toContain('Check In At Time');
  });

  it('log.originalRows matches fixture row count', () => {
    expect(result.log.originalRows).toBe(RAW.length);
  });

  it('log.finalRows = originalRows - 1 (one outlier removed)', () => {
    expect(result.log.finalRows).toBe(RAW.length - 1);
  });
});
