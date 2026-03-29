/**
 * statistics.js
 *
 * Pure statistical functions ported from the Python analytics pipeline.
 * No DOM dependencies — fully testable in Node (Vitest).
 *
 * Implemented in Phase 1 (stubs with full signatures):
 *   quantile(values, q)
 *   iqrOutlierBounds(values, lowerMin)
 *   giniCoefficient(values)
 *
 * Implemented in Phase 2 (requires jstat):
 *   welchTTest(group1, group2)
 *
 * All algorithms must match Python/NumPy/SciPy output within:
 *   - quantile: exact (linear interpolation, same as numpy default)
 *   - Gini: exact
 *   - IQR bounds: exact
 *   - Welch t/df: |Δ| ≤ 1e-6; p: |Δ| ≤ 1e-4
 */

// ---------------------------------------------------------------------------
// Quantile  (linear interpolation — matches numpy/pandas default)
// ---------------------------------------------------------------------------

/**
 * Compute the q-th quantile of an array of numbers using linear interpolation.
 * Equivalent to numpy.quantile(values, q, interpolation='linear').
 *
 * NaN and null values are ignored.
 *
 * @param {number[]} values
 * @param {number}   q  - quantile in [0, 1]
 * @returns {number}
 */
export function quantile(values, q) {
  const sorted = values
    .filter(v => v != null && !Number.isNaN(v))
    .map(Number)
    .sort((a, b) => a - b);

  if (sorted.length === 0) return NaN;
  if (sorted.length === 1) return sorted[0];

  const pos = q * (sorted.length - 1);
  const lo = Math.floor(pos);
  const hi = Math.ceil(pos);
  const frac = pos - lo;

  return sorted[lo] + frac * (sorted[hi] - sorted[lo]);
}

// ---------------------------------------------------------------------------
// IQR outlier bounds
// ---------------------------------------------------------------------------

/**
 * Compute lower and upper outlier fences using the Tukey IQR method.
 *
 * Port of:
 *   data_cleaner.py:remove_outliers   (lowerMin = 0.05 for scheduled)
 *   walkin_cleaner.py:handle_duration_outliers  (lowerMin = 0 for walk-ins)
 *
 * Formula:
 *   lower = max(lowerMin, Q1 - 1.5 * IQR)
 *   upper = Q3 + 1.5 * IQR
 *
 * @param {number[]} values
 * @param {number}   [lowerMin=0]  - floor for the lower bound
 * @returns {{ lower: number, upper: number }}
 */
export function iqrOutlierBounds(values, lowerMin = 0) {
  const q1 = quantile(values, 0.25);
  const q3 = quantile(values, 0.75);
  const iqr = q3 - q1;

  const lower = Math.max(lowerMin, q1 - 1.5 * iqr);
  const upper = q3 + 1.5 * iqr;

  return { lower, upper };
}

/**
 * Filter an array to only rows within the IQR outlier bounds.
 *
 * @param {number[]} values
 * @param {number}   [lowerMin=0]
 * @returns {number[]}
 */
export function removeOutliers(values, lowerMin = 0) {
  const { lower, upper } = iqrOutlierBounds(values, lowerMin);
  return values.filter(v => v != null && !Number.isNaN(v) && v >= lower && v <= upper);
}

// ---------------------------------------------------------------------------
// Gini coefficient
// ---------------------------------------------------------------------------

/**
 * Compute the Gini coefficient of a distribution.
 *
 * Exact port of walkin_metrics.py:calculate_gini_coefficient.
 * Returns 0 for empty arrays or all-zero arrays.
 *
 * @param {number[]} values
 * @returns {number}  in [0, 1]
 */
export function giniCoefficient(values) {
  const sorted = [...values]
    .filter(v => v != null && !Number.isNaN(v))
    .map(Number)
    .sort((a, b) => a - b);

  const n = sorted.length;
  if (n === 0) return 0;

  const total = sorted.reduce((acc, v) => acc + v, 0);
  if (total === 0) return 0;

  let cumsum = 0;
  for (let i = 0; i < n; i++) {
    cumsum += (2 * (i + 1) - n - 1) * sorted[i];
  }

  return cumsum / (n * total);
}

// ---------------------------------------------------------------------------
// Welch's t-test  (implemented in Phase 2 — stub here for import safety)
// ---------------------------------------------------------------------------

/**
 * Perform Welch's two-sample t-test (unequal variances).
 *
 * Uses jstat for the Student-t CDF only; Welch statistic and df are computed
 * explicitly to match scipy.stats.ttest_ind(equal_var=False).
 *
 * NOTE: This function requires the 'jstat' package.  It is a stub in Phase 1
 * and will throw if called before Phase 2 implementation.
 *
 * @param {number[]} group1
 * @param {number[]} group2
 * @returns {{ t: number, df: number, p: number }}
 */
export function welchTTest(group1, group2) {
  // Phase 1 stub — will be fully implemented in Phase 2
  throw new Error('welchTTest: not yet implemented (Phase 2)');
}

// ---------------------------------------------------------------------------
// groupBy helper
// ---------------------------------------------------------------------------

/**
 * Group an array of objects by a key function and aggregate values.
 *
 * @template T, K, V
 * @param {T[]}         rows
 * @param {(row: T) => K}  keyFn
 * @param {(row: T) => V}  valueFn
 * @returns {Map<K, V[]>}
 */
export function groupBy(rows, keyFn, valueFn) {
  const map = new Map();
  for (const row of rows) {
    const key = keyFn(row);
    const val = valueFn(row);
    if (!map.has(key)) map.set(key, []);
    map.get(key).push(val);
  }
  return map;
}
