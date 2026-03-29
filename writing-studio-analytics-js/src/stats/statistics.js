/**
 * statistics.js
 *
 * Pure statistical functions ported from the Python analytics pipeline.
 * No DOM dependencies — fully testable in Node (Vitest).
 *
 *   quantile(values, q)              — linear interpolation (numpy default)
 *   iqrOutlierBounds(values, lowerMin)
 *   removeOutliers(values, lowerMin)
 *   giniCoefficient(values)
 *   welchTTest(group1, group2)       — Welch's t-test via jstat CDF
 *   groupBy(rows, keyFn, valueFn)
 *   sampleVariance(values)
 *
 * Parity requirements vs Python/NumPy/SciPy:
 *   - quantile: exact match (linear interpolation)
 *   - Gini: exact match
 *   - IQR bounds: exact match
 *   - Welch t/df: |Δ| ≤ 1e-6;  p: |Δ| ≤ 1e-4
 */

// jstat is a UMD bundle; Vite/Node can import it as a default or named import.
import jStatPkg from 'jstat';

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
// Sample variance (unbiased, ddof=1 — matches numpy/scipy default)
// ---------------------------------------------------------------------------

/**
 * Unbiased sample variance (divides by n-1).
 * Matches numpy.var(ddof=1) / scipy behaviour.
 *
 * @param {number[]} values
 * @returns {number}
 */
export function sampleVariance(values) {
  const clean = values.filter(v => v != null && !Number.isNaN(v)).map(Number);
  const n = clean.length;
  if (n < 2) return NaN;
  const mean = clean.reduce((s, v) => s + v, 0) / n;
  return clean.reduce((s, v) => s + (v - mean) ** 2, 0) / (n - 1);
}

// ---------------------------------------------------------------------------
// Welch's t-test
// ---------------------------------------------------------------------------

/**
 * Perform Welch's two-sample t-test (unequal variances).
 *
 * Welch statistic and degrees of freedom are computed explicitly to match
 * scipy.stats.ttest_ind(equal_var=False).  The Student-t CDF is evaluated
 * using jstat so that p-value computation is browser-safe.
 *
 * Parity tolerances (vs scipy):
 *   |t_js - t_py|  ≤ 1e-6
 *   |df_js - df_py| ≤ 1e-6
 *   |p_js - p_py|  ≤ 1e-4
 *
 * @param {number[]} group1
 * @param {number[]} group2
 * @returns {{ t: number, df: number, p: number }}
 */
export function welchTTest(group1, group2) {
  const g1 = group1.filter(v => v != null && !Number.isNaN(v)).map(Number);
  const g2 = group2.filter(v => v != null && !Number.isNaN(v)).map(Number);

  const n1 = g1.length;
  const n2 = g2.length;

  if (n1 < 2 || n2 < 2) {
    throw new Error('welchTTest: each group must have at least 2 observations');
  }

  const mean1 = g1.reduce((s, v) => s + v, 0) / n1;
  const mean2 = g2.reduce((s, v) => s + v, 0) / n2;
  const var1 = sampleVariance(g1);
  const var2 = sampleVariance(g2);

  const se = Math.sqrt(var1 / n1 + var2 / n2);
  const t = (mean1 - mean2) / se;

  // Welch–Satterthwaite degrees of freedom
  const v1 = var1 / n1;
  const v2 = var2 / n2;
  const df = (v1 + v2) ** 2 / (v1 ** 2 / (n1 - 1) + v2 ** 2 / (n2 - 1));

  // Two-tailed p-value using jstat Student-t CDF
  // jstat may be exported as default or as { jStat }
  const jStat = jStatPkg.jStat ?? jStatPkg;
  const p = 2 * (1 - jStat.studentt.cdf(Math.abs(t), df));

  return { t, df, p };
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
