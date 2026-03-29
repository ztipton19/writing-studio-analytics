/**
 * fileLoader.test.js
 *
 * Tests for session-type detection and column cleaning.
 * These run in Node (Vitest) without a browser.
 */

import { describe, it, expect } from 'vitest';
import { detectSessionType, cleanColumnNames } from '../src/core/fileLoader.js';
import scheduledFixture from './fixtures/scheduled_headers.json';
import walkinFixture from './fixtures/walkin_headers.json';

// ---------------------------------------------------------------------------
// detectSessionType
// ---------------------------------------------------------------------------

describe('detectSessionType', () => {
  it('identifies scheduled sessions from full header set', () => {
    expect(detectSessionType(scheduledFixture.headers)).toBe('scheduled');
  });

  it('identifies walk-in sessions from full header set', () => {
    expect(detectSessionType(walkinFixture.headers)).toBe('walkin');
  });

  it('detects scheduled with only 2 scheduled indicators', () => {
    const headers = ['Appointment Type', 'Requested Length', 'Student Email'];
    expect(detectSessionType(headers)).toBe('scheduled');
  });

  it('detects walkin with only 2 walkin indicators', () => {
    const headers = ['Check In At Date', 'Check In At Time', 'Student Email'];
    expect(detectSessionType(headers)).toBe('walkin');
  });

  it('returns unknown when no indicators present', () => {
    const headers = ['Column A', 'Column B', 'Column C'];
    expect(detectSessionType(headers)).toBe('unknown');
  });

  it('prefers scheduled when scheduled score >= 2 regardless of walkin score (matches Python logic)', () => {
    const headers = [
      'Appointment Type',
      'Requested Length',
      'Duration Minutes',
      'Check In At Date',
      'Check In At Time',
    ];
    // scheduledScore=2, walkinScore=3 — Python checks scheduled first:
    //   if scheduled_score >= 2: return 'scheduled'
    expect(detectSessionType(headers)).toBe('scheduled');
  });

  it('detects walkin from single indicator when no scheduled indicator present', () => {
    const headers = ['Duration Minutes', 'Student Email', 'Unique ID'];
    expect(detectSessionType(headers)).toBe('walkin');
  });

  it('handles empty header array', () => {
    expect(detectSessionType([])).toBe('unknown');
  });
});

// ---------------------------------------------------------------------------
// cleanColumnNames
// ---------------------------------------------------------------------------

describe('cleanColumnNames', () => {
  it('strips leading whitespace', () => {
    expect(cleanColumnNames(['  Student Email'])).toEqual(['Student Email']);
  });

  it('strips trailing whitespace', () => {
    expect(cleanColumnNames(['Student Email  '])).toEqual(['Student Email']);
  });

  it('strips both sides', () => {
    expect(cleanColumnNames(['  Tutor Email  '])).toEqual(['Tutor Email']);
  });

  it('does not modify already-clean names', () => {
    const clean = ['Student Email', 'Unique ID', 'Status'];
    expect(cleanColumnNames(clean)).toEqual(clean);
  });

  it('handles Penji trailing-space pattern (first appointment column)', () => {
    // Penji exports "Agenda - Is this your first appointment? " with a trailing space
    const input = ['Agenda - Is this your first appointment? '];
    expect(cleanColumnNames(input)).toEqual(['Agenda - Is this your first appointment?']);
  });

  it('handles empty array', () => {
    expect(cleanColumnNames([])).toEqual([]);
  });

  it('coerces non-string values to string and trims', () => {
    expect(cleanColumnNames([null, undefined, 123])).toEqual(['null', 'undefined', '123']);
  });
});
