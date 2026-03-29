/**
 * privacy.js
 *
 * PII detection, SHA-256 anonymisation, and PBKDF2-encrypted codebook.
 * Port of src/core/privacy.py, adapted for Web Crypto API.
 *
 * IMPORTANT COMPATIBILITY NOTE
 * The Python app uses Fernet (AES-CBC).  This JS version uses AES-GCM.
 * The two formats are not cross-compatible.  Any codebook created by the
 * Python app must be re-generated once when switching to this JS app.
 * Codebook save format:  { version: 2, iv: "<base64>", ciphertext: "<base64>" }
 *
 * Public async API:
 *   sha256Hex(str)                            → hex string
 *   studentAnonId(email)                      → "STU_NNNNN"
 *   tutorAnonId(email)                        → "TUT_NNNN"
 *   detectPiiColumns(headers, rows)           → string[]
 *   anonymizeWithCodebook(rows, opts)         → { rows, codebook, log }
 *   encryptCodebook(codebook, password)       → base64-JSON payload string
 *   decryptCodebook(payloadStr, password)     → codebook object
 *   lookupInCodebook(anonId, payloadStr, pwd) → email string
 *   getCodebookInfo(payloadStr, password)     → metadata object
 */

// ---------------------------------------------------------------------------
// Crypto helpers
// ---------------------------------------------------------------------------

const SALT_STR   = 'writing_studio_analytics_2025';
const SALT_BYTES = new TextEncoder().encode(SALT_STR);
const PBKDF2_ITERS = 100_000;

/**
 * Compute SHA-256 of a UTF-8 string and return lower-case hex.
 * Matches Python: hashlib.sha256(str.encode()).hexdigest()
 *
 * @param {string} str
 * @returns {Promise<string>}
 */
export async function sha256Hex(str) {
  const buf = await crypto.subtle.digest(
    'SHA-256',
    new TextEncoder().encode(str)
  );
  return Array.from(new Uint8Array(buf))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}

/**
 * Derive an AES-GCM CryptoKey from a password using PBKDF2.
 * Fixed salt matches Python constant.
 *
 * @param {string} password
 * @returns {Promise<CryptoKey>}
 */
async function deriveKey(password) {
  const keyMaterial = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(password),
    { name: 'PBKDF2' },
    false,
    ['deriveKey']
  );
  return crypto.subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt: SALT_BYTES,
      iterations: PBKDF2_ITERS,
      hash: 'SHA-256',
    },
    keyMaterial,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt']
  );
}

/** @param {ArrayBuffer} buf @returns {string} */
function toBase64(buf) {
  return btoa(String.fromCharCode(...new Uint8Array(buf)));
}

/** @param {string} b64 @returns {Uint8Array} */
function fromBase64(b64) {
  return Uint8Array.from(atob(b64), c => c.charCodeAt(0));
}

// ---------------------------------------------------------------------------
// ID generation  (matches Python privacy.py exactly)
// ---------------------------------------------------------------------------

/**
 * Generate deterministic anonymous student ID from email.
 * Matches Python: f"STU_{int(hex[:8], 16) % 100000:05d}"
 *
 * @param {string} email
 * @returns {Promise<string>}  e.g. "STU_02769"
 */
export async function studentAnonId(email) {
  const hex = await sha256Hex(String(email));
  const n   = parseInt(hex.slice(0, 8), 16) % 100_000;
  return `STU_${String(n).padStart(5, '0')}`;
}

/**
 * Generate deterministic anonymous tutor ID from email.
 * Matches Python: f"TUT_{int(hex[:8], 16) % 10000:04d}"
 *
 * @param {string} email
 * @returns {Promise<string>}  e.g. "TUT_0842"
 */
export async function tutorAnonId(email) {
  const hex = await sha256Hex(String(email));
  const n   = parseInt(hex.slice(0, 8), 16) % 10_000;
  return `TUT_${String(n).padStart(4, '0')}`;
}

// ---------------------------------------------------------------------------
// PII detection  (mirrors privacy.py:detect_pii_columns)
// ---------------------------------------------------------------------------

const KNOWN_PII = new Set([
  'Student Email', 'Student SSO ID', 'Student - Student ID', 'Student ID', 'Student Name',
  'Tutor Name', 'Tutor Email', 'Tutor SSO ID',
  'Tutor - Email the session receipt to',
  'Canceller Email', 'Requested Tutor Name',
]);

const PII_KEYWORDS = ['email', 'sso', 'student id', 'name'];
const EMAIL_RE     = /[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}/;
const SSO_RE       = /^[a-zA-Z0-9]{6,10}$/;
const NAME_RE      = /^[A-Z][a-z]+ [A-Z][a-z]+.*$/;

/**
 * Two-layer PII detection.
 * Layer 1: exact column-name match.
 * Layer 2: keyword + data-pattern check.
 *
 * @param {string[]} headers  - column names
 * @param {object[]} rows     - data rows (used for pattern sampling)
 * @returns {string[]}
 */
export function detectPiiColumns(headers, rows) {
  const pii = new Set();

  // Layer 1: exact match
  for (const h of headers) {
    if (KNOWN_PII.has(h)) pii.add(h);
  }

  // Layer 2: keyword + data pattern
  for (const h of headers) {
    if (pii.has(h)) continue;
    const lower = h.toLowerCase();
    if (!PII_KEYWORDS.some(kw => lower.includes(kw))) continue;

    // Sample up to 10 non-empty values from this column
    const sample = rows
      .map(r => r[h])
      .filter(v => v != null && v !== '')
      .slice(0, 10);

    if (sample.length === 0) continue;

    const isPii =
      sample.some(v => EMAIL_RE.test(String(v))) ||
      sample.some(v => SSO_RE.test(String(v)))    ||
      sample.some(v => NAME_RE.test(String(v)));

    if (isPii) pii.add(h);
  }

  return [...pii];
}

// ---------------------------------------------------------------------------
// Anonymisation pipeline  (mirrors privacy.py:anonymize_with_codebook)
// ---------------------------------------------------------------------------

/**
 * @typedef {Object} AnonymizeOptions
 * @property {boolean} [createCodebook=true]
 * @property {string}  [password]         - required when createCodebook is true
 * @property {string}  [confirmPassword]  - required when createCodebook is true
 * @property {'scheduled'|'walkin'} [sessionType='scheduled']
 */

/**
 * Anonymise PII columns and optionally build an encrypted codebook payload.
 *
 * @param {object[]}         rows
 * @param {AnonymizeOptions} opts
 * @returns {Promise<{ rows: object[], codebookPayload: string|null, log: object }>}
 */
export async function anonymizeWithCodebook(rows, opts = {}) {
  const {
    createCodebook    = true,
    password          = null,
    confirmPassword   = null,
    sessionType       = 'scheduled',
  } = opts;

  // Validate password
  if (createCodebook) {
    if (!password)                        throw new Error('Password required to create codebook.');
    if (password !== confirmPassword)     throw new Error('Passwords do not match! Please re-enter matching passwords.');
    if (password.length < 12)            throw new Error('Password must be at least 12 characters for security.');
  }

  const headers = rows.length > 0 ? Object.keys(rows[0]) : [];

  const codebookData = {
    students: {},
    tutors:   {},
    metadata: {
      created:          new Date().toISOString(),
      session_type:     sessionType,
      total_students:   0,
      total_tutors:     0,
      dataset_date_range: null,
    },
  };

  const log = {
    piiColumnsRemoved:   [],
    studentsAnonymized:  0,
    tutorsAnonymized:    0,
    codebookCreated:     createCodebook,
    studentCollisions:   0,
    tutorCollisions:     0,
    sessionType,
  };

  // Determine date range from available date column
  const dateCol =
    headers.includes('Requested At Date')  ? 'Requested At Date' :
    headers.includes('Check In At Date')   ? 'Check In At Date'  :
    headers.includes('Booking_DateTime')   ? 'Booking_DateTime'  :
    headers.includes('Check_In_DateTime')  ? 'Check_In_DateTime' : null;

  if (dateCol) {
    const dates = rows
      .map(r => r[dateCol])
      .filter(Boolean)
      .map(d => (d instanceof Date ? d : new Date(d)))
      .filter(d => !isNaN(d));
    if (dates.length) {
      const min = new Date(Math.min(...dates));
      const max = new Date(Math.max(...dates));
      codebookData.metadata.dataset_date_range =
        `${min.toISOString().slice(0, 10)} to ${max.toISOString().slice(0, 10)}`;
    }
  }

  let outRows = rows.map(r => ({ ...r }));

  // ── Anonymise students ────────────────────────────────────────────────────
  const studentEmailCol =
    headers.includes('Student Email') ? 'Student Email' :
    headers.includes('Student - Email') ? 'Student - Email' : null;

  if (studentEmailCol) {
    const uniqueEmails = [...new Set(
      rows.map(r => r[studentEmailCol]).filter(v => v != null && v !== '')
    )];

    const studentMap = new Map();       // email → anonId
    const usedStudentIds = new Set();
    let studentCollisions = 0;

    for (const email of uniqueEmails) {
      let id = await studentAnonId(email);

      if (usedStudentIds.has(id)) {
        studentCollisions++;
        let suffix = 'A';
        while (usedStudentIds.has(`${id}_${suffix}`)) {
          suffix = String.fromCharCode(suffix.charCodeAt(0) + 1);
        }
        id = `${id}_${suffix}`;
      }

      usedStudentIds.add(id);
      studentMap.set(email, id);
      if (createCodebook) codebookData.students[id] = email;
    }

    outRows = outRows.map(r => ({
      ...r,
      Student_Anon_ID: studentMap.get(r[studentEmailCol]) ?? null,
    }));

    log.studentsAnonymized = studentMap.size;
    log.studentCollisions  = studentCollisions;
    codebookData.metadata.total_students = studentMap.size;
  }

  // ── Anonymise tutors ──────────────────────────────────────────────────────
  const tutorEmailCol =
    headers.includes('Tutor Email')                            ? 'Tutor Email' :
    headers.includes('Tutor - Email the session receipt to')   ? 'Tutor - Email the session receipt to' : null;

  const hasTutorData = tutorEmailCol &&
    rows.some(r => r[tutorEmailCol] != null && r[tutorEmailCol] !== '');

  if (hasTutorData) {
    const uniqueEmails = [...new Set(
      rows.map(r => r[tutorEmailCol]).filter(v => v != null && v !== '')
    )];

    const tutorMap = new Map();
    const usedTutorIds = new Set();
    let tutorCollisions = 0;

    for (const email of uniqueEmails) {
      let id = await tutorAnonId(email);

      if (usedTutorIds.has(id)) {
        tutorCollisions++;
        let suffix = 'A';
        while (usedTutorIds.has(`${id}_${suffix}`)) {
          suffix = String.fromCharCode(suffix.charCodeAt(0) + 1);
        }
        id = `${id}_${suffix}`;
      }

      usedTutorIds.add(id);
      tutorMap.set(email, id);
      if (createCodebook) codebookData.tutors[id] = email;
    }

    outRows = outRows.map(r => ({
      ...r,
      Tutor_Anon_ID: tutorMap.get(r[tutorEmailCol]) ?? null,
    }));

    log.tutorsAnonymized = tutorMap.size;
    log.tutorCollisions  = tutorCollisions;
    codebookData.metadata.total_tutors = tutorMap.size;
  }

  // ── Remove all PII columns ────────────────────────────────────────────────
  const piiCols = detectPiiColumns(headers, rows);
  const piiSet  = new Set(piiCols);

  outRows = outRows.map(r => {
    const out = {};
    for (const [k, v] of Object.entries(r)) {
      if (!piiSet.has(k)) out[k] = v;
    }
    return out;
  });

  log.piiColumnsRemoved = piiCols;

  // ── Encrypt codebook ──────────────────────────────────────────────────────
  let codebookPayload = null;
  if (createCodebook) {
    codebookPayload = await encryptCodebook(codebookData, password);
  }

  return { rows: outRows, codebookPayload, log };
}

// ---------------------------------------------------------------------------
// Codebook encryption / decryption
// ---------------------------------------------------------------------------

/**
 * Encrypt a codebook object with AES-GCM + PBKDF2 key.
 *
 * @param {object} codebook
 * @param {string} password
 * @returns {Promise<string>}  JSON string with { version, iv, ciphertext }
 */
export async function encryptCodebook(codebook, password) {
  const key      = await deriveKey(password);
  const iv       = crypto.getRandomValues(new Uint8Array(12)); // 96-bit IV for AES-GCM
  const plaintext = new TextEncoder().encode(JSON.stringify(codebook));

  const cipherBuf = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    plaintext
  );

  return JSON.stringify({
    version:    2,
    iv:         toBase64(iv),
    ciphertext: toBase64(cipherBuf),
  });
}

/**
 * Decrypt a codebook payload string.
 *
 * @param {string} payloadStr - JSON string produced by encryptCodebook
 * @param {string} password
 * @returns {Promise<object>}
 * @throws {Error} with user-facing message on wrong password or corrupt data
 */
export async function decryptCodebook(payloadStr, password) {
  let payload;
  try {
    payload = JSON.parse(payloadStr);
  } catch {
    throw new Error('CORRUPTED CODEBOOK\nThe codebook file appears to be corrupted or invalid.');
  }

  if (payload.version !== 2) {
    throw new Error(
      `Unsupported codebook version: ${payload.version}.\n` +
      'This codebook was created with a different version of the app.'
    );
  }

  const key = await deriveKey(password);
  const iv  = fromBase64(payload.iv);
  const ct  = fromBase64(payload.ciphertext);

  let plainBuf;
  try {
    plainBuf = await crypto.subtle.decrypt({ name: 'AES-GCM', iv }, key, ct);
  } catch {
    throw new Error(
      'INCORRECT PASSWORD\n' +
      'The password you entered does not match the codebook encryption.\n' +
      'Please try again with the correct password.'
    );
  }

  try {
    return JSON.parse(new TextDecoder().decode(plainBuf));
  } catch {
    throw new Error('CORRUPTED CODEBOOK\nThe codebook JSON is invalid after decryption.');
  }
}

// ---------------------------------------------------------------------------
// Lookup / info  (mirrors privacy.py:lookup_in_codebook / get_codebook_info)
// ---------------------------------------------------------------------------

/**
 * Reverse-lookup an anonymous ID to its original email.
 *
 * @param {string} anonId      - "STU_NNNNN" or "TUT_NNNN"
 * @param {string} payloadStr  - encrypted codebook JSON
 * @param {string} password
 * @returns {Promise<string>}  original email, or throws on failure
 */
export async function lookupInCodebook(anonId, payloadStr, password) {
  if (!anonId.startsWith('STU_') && !anonId.startsWith('TUT_')) {
    throw new Error("Invalid ID format. Must start with 'STU_' or 'TUT_'.");
  }

  const codebook = await decryptCodebook(payloadStr, password);

  const section = anonId.startsWith('STU_') ? codebook.students : codebook.tutors;
  const result  = section?.[anonId];

  if (!result) {
    const kind = anonId.startsWith('STU_') ? 'Student' : 'Tutor';
    throw new Error(`${kind} ID '${anonId}' not found in codebook.`);
  }

  return result;
}

/**
 * Get codebook metadata without revealing individual entries.
 *
 * @param {string} payloadStr
 * @param {string} password
 * @returns {Promise<object>}
 */
export async function getCodebookInfo(payloadStr, password) {
  const cb = await decryptCodebook(payloadStr, password);
  return {
    session_type:     cb.metadata?.session_type   ?? 'unknown',
    total_students:   cb.metadata?.total_students ?? 0,
    total_tutors:     cb.metadata?.total_tutors   ?? 0,
    created:          cb.metadata?.created        ?? 'Unknown',
    date_range:       cb.metadata?.dataset_date_range ?? 'Unknown',
  };
}
