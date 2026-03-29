/**
 * columnMapping.js
 *
 * Loads the column_mapping.json spec, validates an uploaded dataset's headers
 * against required and optional columns, and normalises (renames) headers to
 * the canonical "target" names used throughout the rest of the app.
 *
 * Public API:
 *   loadMapping()                       → Promise<mapping>
 *   validateColumns(headers, sessionType, mapping)  → ValidationResult
 *   normalizeColumns(rows, headers, sessionType, mapping) → { rows, headers }
 */

// ---------------------------------------------------------------------------
// Types (JSDoc)
// ---------------------------------------------------------------------------
/**
 * @typedef {Object} MappingEntry
 * @property {string}   label    - Human-readable label
 * @property {string}   target   - Canonical column name used in analytics code
 * @property {string}   source   - Expected Penji export column name
 * @property {string[]} [aliases]- Alternative source names (old Penji formats)
 * @property {string}   category
 * @property {boolean}  required
 */

/**
 * @typedef {Object} ColumnMapping
 * @property {MappingEntry[]} scheduled
 * @property {MappingEntry[]} walkin
 */

/**
 * @typedef {Object} ValidationResult
 * @property {boolean}        valid           - false if any required column is missing
 * @property {string[]}       presentRequired - required columns found
 * @property {string[]}       missingRequired - required columns not found
 * @property {string[]}       presentOptional - optional columns found
 * @property {string[]}       missingOptional - optional columns not found
 * @property {string[]}       extraColumns    - columns in file not in the mapping
 * @property {Object<string,string>} sourceToTarget - source→target rename map
 */

// ---------------------------------------------------------------------------
// Load mapping
// ---------------------------------------------------------------------------

/** Cached mapping so we only fetch once per session. */
let _cachedMapping = null;

/**
 * Load column_mapping.json.
 * In the bundled single-file build this JSON is inlined by Vite; during dev it
 * is fetched from the project root.
 * @returns {Promise<ColumnMapping>}
 */
export async function loadMapping() {
  if (_cachedMapping) return _cachedMapping;

  // Dynamic import works for both dev (HTTP) and the singlefile build (inlined)
  const mapping = await import('/column_mapping.json', { assert: { type: 'json' } })
    .then(m => m.default)
    .catch(async () => {
      // Fallback: plain fetch (some browsers / Vite configs prefer this)
      const res = await fetch('./column_mapping.json');
      if (!res.ok) throw new Error('Failed to load column_mapping.json');
      return res.json();
    });

  _cachedMapping = mapping;
  return mapping;
}

// ---------------------------------------------------------------------------
// Validate columns
// ---------------------------------------------------------------------------

/**
 * Build a set of all source names (+ aliases) that map to a given target,
 * for efficient reverse lookup.
 *
 * Returns a Map from every known source/alias string → MappingEntry.
 * @param {MappingEntry[]} entries
 * @returns {Map<string, MappingEntry>}
 */
function buildSourceIndex(entries) {
  const idx = new Map();
  for (const entry of entries) {
    idx.set(entry.source, entry);
    if (Array.isArray(entry.aliases)) {
      for (const alias of entry.aliases) idx.set(alias, entry);
    }
  }
  return idx;
}

/**
 * Validate file headers against the mapping spec for the detected session type.
 *
 * @param {string[]}      headers     - Cleaned column names from the file
 * @param {'scheduled'|'walkin'|'unknown'} sessionType
 * @param {ColumnMapping} mapping
 * @returns {ValidationResult}
 */
export function validateColumns(headers, sessionType, mapping) {
  const entries = mapping[sessionType] ?? [];
  const sourceIndex = buildSourceIndex(entries);
  const headerSet = new Set(headers);

  const presentRequired = [];
  const missingRequired = [];
  const presentOptional = [];
  const missingOptional = [];
  const sourceToTarget = {};

  for (const entry of entries) {
    // Find which name is present in the file (source, or any alias)
    const allNames = [entry.source, ...(entry.aliases ?? [])];
    const foundName = allNames.find(n => headerSet.has(n));

    if (foundName) {
      sourceToTarget[foundName] = entry.target;
      if (entry.required) {
        presentRequired.push(entry.target);
      } else {
        presentOptional.push(entry.target);
      }
    } else {
      if (entry.required) {
        missingRequired.push(entry.target);
      } else {
        missingOptional.push(entry.target);
      }
    }
  }

  // Extra columns: in file but not in any mapping source/alias
  const extraColumns = headers.filter(h => !sourceIndex.has(h));

  const valid = missingRequired.length === 0;

  return {
    valid,
    presentRequired,
    missingRequired,
    presentOptional,
    missingOptional,
    extraColumns,
    sourceToTarget,
  };
}

// ---------------------------------------------------------------------------
// Normalise columns
// ---------------------------------------------------------------------------

/**
 * Rename source column names to their canonical target names.
 *
 * Rows that have extra (unmapped) columns are preserved as-is so no data is
 * silently dropped before later pipeline stages.
 *
 * @param {object[]}  rows
 * @param {string[]}  headers
 * @param {Object<string,string>} sourceToTarget - from validateColumns
 * @returns {{ rows: object[], headers: string[] }}
 */
export function normalizeColumns(rows, headers, sourceToTarget) {
  const newHeaders = headers.map(h => sourceToTarget[h] ?? h);

  const newRows = rows.map(row => {
    const newRow = {};
    headers.forEach((src, i) => {
      newRow[newHeaders[i]] = row[src];
    });
    return newRow;
  });

  return { rows: newRows, headers: newHeaders };
}
