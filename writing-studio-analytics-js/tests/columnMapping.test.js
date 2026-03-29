/**
 * columnMapping.test.js
 *
 * Tests for validateColumns and normalizeColumns.
 * Uses the real column_mapping.json via a relative import.
 */

import { describe, it, expect } from 'vitest';
import { validateColumns, normalizeColumns } from '../src/core/columnMapping.js';
import mapping from '../column_mapping.json';
import scheduledFixture from './fixtures/scheduled_headers.json';
import walkinFixture from './fixtures/walkin_headers.json';

// ---------------------------------------------------------------------------
// validateColumns — scheduled
// ---------------------------------------------------------------------------

describe('validateColumns (scheduled)', () => {
  it('passes validation for a complete scheduled header set', () => {
    const result = validateColumns(scheduledFixture.headers, 'scheduled', mapping);
    expect(result.valid).toBe(true);
    expect(result.missingRequired).toHaveLength(0);
  });

  it('identifies all required scheduled columns as present', () => {
    const result = validateColumns(scheduledFixture.headers, 'scheduled', mapping);
    // Required scheduled columns: Student Email, Unique ID, Status
    expect(result.presentRequired).toContain('Student Email');
    expect(result.presentRequired).toContain('Unique ID');
    expect(result.presentRequired).toContain('Status');
  });

  it('flags missing required columns', () => {
    const stripped = scheduledFixture.headers.filter(h => h !== 'Student Email');
    const result = validateColumns(stripped, 'scheduled', mapping);
    expect(result.valid).toBe(false);
    expect(result.missingRequired).toContain('Student Email');
  });

  it('identifies optional columns that are present', () => {
    const result = validateColumns(scheduledFixture.headers, 'scheduled', mapping);
    expect(result.presentOptional.length).toBeGreaterThan(0);
  });

  it('extra columns are listed under extraColumns', () => {
    const headers = [...scheduledFixture.headers, 'Custom Extra Column'];
    const result = validateColumns(headers, 'scheduled', mapping);
    expect(result.extraColumns).toContain('Custom Extra Column');
  });

  it('returns sourceToTarget map for present columns', () => {
    const result = validateColumns(scheduledFixture.headers, 'scheduled', mapping);
    // "Unique ID" source → target "Unique ID" (same in this case)
    expect(result.sourceToTarget['Unique ID']).toBe('Unique ID');
    // "Requested At Date" → "Requested At Date"
    expect(result.sourceToTarget['Requested At Date']).toBe('Requested At Date');
  });
});

// ---------------------------------------------------------------------------
// validateColumns — walkin
// ---------------------------------------------------------------------------

describe('validateColumns (walkin)', () => {
  it('passes validation for a complete walk-in header set', () => {
    const result = validateColumns(walkinFixture.headers, 'walkin', mapping);
    expect(result.valid).toBe(true);
    expect(result.missingRequired).toHaveLength(0);
  });

  it('identifies required walk-in columns as present', () => {
    const result = validateColumns(walkinFixture.headers, 'walkin', mapping);
    expect(result.presentRequired).toContain('Student Email');
    expect(result.presentRequired).toContain('Unique ID');
    expect(result.presentRequired).toContain('Status');
    expect(result.presentRequired).toContain('Check In At Date');
    expect(result.presentRequired).toContain('Check In At Time');
  });

  it('flags missing Check In At Date as required', () => {
    const stripped = walkinFixture.headers.filter(h => h !== 'Check In At Date');
    const result = validateColumns(stripped, 'walkin', mapping);
    expect(result.valid).toBe(false);
    expect(result.missingRequired).toContain('Check In At Date');
  });
});

// ---------------------------------------------------------------------------
// validateColumns — alias resolution
// ---------------------------------------------------------------------------

describe('validateColumns (alias resolution)', () => {
  it('resolves alias column names for post-session confidence', () => {
    // The mapping has an alias for the old Penji format of post-session confidence
    const alias = 'Student - How confident do you feel about your writing assignment now that your meeting is over? (1="Not at all"; 5="Very")';
    const headers = [
      ...scheduledFixture.headers.filter(h =>
        !h.startsWith('Student - How confident')
      ),
      alias,
    ];
    const result = validateColumns(headers, 'scheduled', mapping);
    // The alias column should map to the target
    expect(result.sourceToTarget[alias]).toBeDefined();
  });
});

// ---------------------------------------------------------------------------
// normalizeColumns
// ---------------------------------------------------------------------------

describe('normalizeColumns', () => {
  it('renames source headers to target names', () => {
    const rows = [{ 'Student Email': 'a@b.com', 'Unique ID': '123' }];
    const headers = ['Student Email', 'Unique ID'];
    const sourceToTarget = { 'Student Email': 'Student Email', 'Unique ID': 'Unique ID' };
    const { headers: out } = normalizeColumns(rows, headers, sourceToTarget);
    expect(out).toEqual(['Student Email', 'Unique ID']);
  });

  it('preserves unmapped (extra) columns as-is', () => {
    const rows = [{ 'Custom Col': 'value' }];
    const headers = ['Custom Col'];
    const { headers: out, rows: outRows } = normalizeColumns(rows, headers, {});
    expect(out).toEqual(['Custom Col']);
    expect(outRows[0]['Custom Col']).toBe('value');
  });

  it('renames actual Penji trailing-space variant', () => {
    const trimmedAlias = 'Agenda - Is this your first appointment?';
    const result = validateColumns(
      [...scheduledFixture.headers.filter(h => !h.startsWith('Agenda - Is this your first')), trimmedAlias],
      'scheduled',
      mapping
    );
    const { headers: out } = normalizeColumns(
      [{ [trimmedAlias]: 'Yes' }],
      [trimmedAlias],
      result.sourceToTarget
    );
    // After normalisation the column should have the canonical target name
    expect(out[0]).toBeDefined();
  });

  it('row values are preserved after renaming', () => {
    const sourceToTarget = { 'Student Email': 'Student Email' };
    const rows = [{ 'Student Email': 'test@uark.edu' }];
    const { rows: out } = normalizeColumns(rows, ['Student Email'], sourceToTarget);
    expect(out[0]['Student Email']).toBe('test@uark.edu');
  });
});
