/**
 * payloadSanitizer.js — Enterprise Payload Sanitizer for SupplyShield AI
 *
 * Recursively cleans request payloads before sending them to FastAPI:
 * 1. Trims string values.
 * 2. Removes empty string "" properties or converts them to null if appropriate.
 * 3. Filters out incomplete/empty objects from arrays (e.g., [{ name: "", email: "" }] → []).
 * 4. Removes empty nested placeholder objects.
 * 5. Removes undefined properties.
 */

export function isObject(val) {
  return val !== null && typeof val === 'object' && !Array.isArray(val);
}

export function isObjectEmpty(obj) {
  if (!isObject(obj)) return true;
  return Object.values(obj).every(v => v === null || v === undefined || v === '' || (Array.isArray(v) && v.length === 0) || (isObject(v) && isObjectEmpty(v)));
}

export function sanitizePayload(val, options = {}) {
  const { preserveEmptyStrings = false, removeNulls = false } = options;

  if (val === undefined) return undefined;

  if (typeof val === 'string') {
    const trimmed = val.trim();
    if (trimmed === '' && !preserveEmptyStrings) return null;
    return trimmed;
  }

  if (Array.isArray(val)) {
    const cleaned = val
      .map(item => sanitizePayload(item, options))
      .filter(item => {
        if (item === null || item === undefined) return false;
        if (isObject(item) && isObjectEmpty(item)) return false;
        return true;
      });
    return cleaned;
  }

  if (isObject(val)) {
    const res = {};
    for (const [key, value] of Object.entries(val)) {
      const sanitized = sanitizePayload(value, options);
      
      // Skip undefined or empty nested objects
      if (sanitized === undefined) continue;
      if (removeNulls && sanitized === null) continue;
      if (isObject(sanitized) && isObjectEmpty(sanitized)) continue;
      
      res[key] = sanitized;
    }
    return res;
  }

  return val;
}
