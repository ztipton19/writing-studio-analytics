/**
 * statistics.test.js
 *
 * Parity tests for statistics.js against Python/NumPy/SciPy golden values.
 * Tolerance: quantile & Gini exact (within floating-point epsilon);
 *            IQR bounds exact; Welch t-test tested in Phase 2.
 */

import { describe, it, expect } from 'vitest';
import { quantile, iqrOutlierBounds, removeOutliers, giniCoefficient } from '../src/stats/statistics.js';
import parityFixture from './fixtures/statistics_parity.json';

const FLOAT_TOL = 1e-9;

// ---------------------------------------------------------------------------
// quantile
// ---------------------------------------------------------------------------

describe('quantile (linear interpolation)', () => {
  parityFixture.quantile.forEach(({ name, values, q, expected }) => {
    it(`${name}: quantile(${JSON.stringify(values)}, ${q}) ≈ ${expected}`, () => {
      expect(quantile(values, q)).toBeCloseTo(expected, 10);
    });
  });

  it('returns exact value for q=0 (min)', () => {
    expect(quantile([3, 1, 4, 1, 5], 0)).toBe(1);
  });

  it('returns exact value for q=1 (max)', () => {
    expect(quantile([3, 1, 4, 1, 5], 1)).toBe(5);
  });

  it('returns NaN for empty array', () => {
    expect(quantile([], 0.5)).toBeNaN();
  });

  it('returns single value for single-element array', () => {
    expect(quantile([42], 0.5)).toBe(42);
  });

  it('ignores null values', () => {
    expect(quantile([null, 1, 2, 3, null], 0.5)).toBe(2);
  });

  it('ignores NaN values', () => {
    expect(quantile([NaN, 1, 2, 3, NaN], 0.5)).toBe(2);
  });
});

// ---------------------------------------------------------------------------
// iqrOutlierBounds
// ---------------------------------------------------------------------------

describe('iqrOutlierBounds', () => {
  it('scheduled sessions — lower floored at lowerMin=0.05', () => {
    const values = [0.33, 0.5, 0.5, 0.67, 0.75, 0.83, 1.0, 1.0, 1.25, 1.5];
    const { lower, upper } = iqrOutlierBounds(values, 0.05);
    // Q1=0.5425, Q3=1.0, IQR=0.4575 → raw lower=0.5425-0.68625=-0.14375 → max(0.05,-0.14375)=0.05
    expect(lower).toBeCloseTo(0.05, 10);
    // upper = 1.0 + 1.5*0.4575 = 1.68625
    expect(upper).toBeCloseTo(1.68625, 10);
  });

  it('walk-in minutes — lower floored at 0', () => {
    const values = [5, 10, 15, 20, 25, 30, 35, 40, 45, 60];
    const { lower, upper } = iqrOutlierBounds(values, 0);
    // Q1=16.25, Q3=38.75, IQR=22.5 → lower=max(0,16.25-33.75)=0; upper=38.75+33.75=72.5
    expect(lower).toBe(0);
    expect(upper).toBeCloseTo(72.5, 10);
  });

  it('default lowerMin=0 when not specified', () => {
    const values = [1, 2, 3, 4, 5];
    const { lower } = iqrOutlierBounds(values);
    // Q1=1.75, Q3=4.25, IQR=2.5; raw lower=1.75-3.75=-2; max(0,-2)=0
    expect(lower).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// removeOutliers
// ---------------------------------------------------------------------------

describe('removeOutliers', () => {
  it('removes values outside IQR fences', () => {
    // Adding extreme outliers to a dataset
    const values = [0.5, 0.5, 0.67, 0.75, 0.83, 1.0, 1.0, 5.0, 0.001];
    const cleaned = removeOutliers(values, 0.05);
    expect(cleaned).not.toContain(5.0);
    expect(cleaned).not.toContain(0.001);
  });

  it('keeps values exactly at the fence (inclusive)', () => {
    // If upper bound = 1.75, a value of 1.75 should be kept
    const values = [0.33, 0.5, 0.5, 0.67, 0.75, 0.83, 1.0, 1.0, 1.25, 1.5];
    const { upper } = iqrOutlierBounds(values, 0.05);
    const withFence = [...values, upper];
    const cleaned = removeOutliers(withFence, 0.05);
    expect(cleaned).toContain(upper);
  });

  it('returns empty array for empty input', () => {
    expect(removeOutliers([], 0.05)).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// giniCoefficient
// ---------------------------------------------------------------------------

describe('giniCoefficient', () => {
  parityFixture.gini.forEach(({ name, values, expected }) => {
    it(`${name}: gini(${JSON.stringify(values)}) ≈ ${expected}`, () => {
      expect(giniCoefficient(values)).toBeCloseTo(expected, 8);
    });
  });

  it('returns 0 for empty array', () => {
    expect(giniCoefficient([])).toBe(0);
  });

  it('returns 0 for all-zeros array', () => {
    expect(giniCoefficient([0, 0, 0])).toBe(0);
  });

  it('returns 0 for single element', () => {
    expect(giniCoefficient([10])).toBe(0);
  });

  it('result is in [0, 1] for any non-negative input', () => {
    const g = giniCoefficient([1, 3, 5, 7, 9, 100]);
    expect(g).toBeGreaterThanOrEqual(0);
    expect(g).toBeLessThanOrEqual(1);
  });

  it('ignores null and NaN values', () => {
    const withNulls = [null, 10, 10, 10, NaN, 10];
    expect(giniCoefficient(withNulls)).toBeCloseTo(0, 8);
  });
});
