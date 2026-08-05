/**
 * ACTIVUM — Frontend Auth Module
 *
 * Implements the two-step HMAC + Bearer token auth flow from GEMINI.md §5:
 *
 * Step 1: POST /auth/token with HMAC-SHA256 signed headers
 * Step 2: GET / with Authorization: Bearer <token>
 *
 * Passthrough mode: if VITE_API_KEY or VITE_API_SIGNING_SECRET are not set,
 * requests are sent without auth headers (matches API passthrough mode).
 *
 * Token caching: tokens are cached in sessionStorage with a 30-second
 * safety buffer before their actual expiry.
 */

const API_KEY = (import.meta.env.VITE_API_KEY || '').trim();
const API_SIGNING_SECRET = (import.meta.env.VITE_API_SIGNING_SECRET || '').trim();
const SESSION_KEY = 'activum_auth_token';
const TTL_SAFETY_BUFFER_S = 30; // Refresh token 30s before it expires

// ---------------------------------------------------------------------------
// Auth mode detection
// ---------------------------------------------------------------------------

export function isAuthEnabled() {
  return Boolean(API_KEY && API_SIGNING_SECRET);
}

// ---------------------------------------------------------------------------
// HMAC-SHA256 signing (Web Crypto API — no external deps)
// ---------------------------------------------------------------------------

async function signHmac(secret, message) {
  const encoder = new TextEncoder();
  const keyData = encoder.encode(secret);
  const msgData = encoder.encode(message);

  const cryptoKey = await crypto.subtle.importKey(
    'raw',
    keyData,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );

  const signature = await crypto.subtle.sign('HMAC', cryptoKey, msgData);
  return Array.from(new Uint8Array(signature))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}

// ---------------------------------------------------------------------------
// Token caching
// ---------------------------------------------------------------------------

function getCachedToken() {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const { token, expiresAt } = JSON.parse(raw);
    if (Date.now() < expiresAt - TTL_SAFETY_BUFFER_S * 1000) {
      return token;
    }
    sessionStorage.removeItem(SESSION_KEY);
    return null;
  } catch {
    return null;
  }
}

function cacheToken(token, ttlSeconds) {
  try {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify({
      token,
      expiresAt: Date.now() + ttlSeconds * 1000,
    }));
  } catch {
    // sessionStorage might be unavailable (e.g. private browsing)
  }
}

// ---------------------------------------------------------------------------
// Token request
// ---------------------------------------------------------------------------

async function fetchToken(apiUrl) {
  const timestamp = String(Math.floor(Date.now() / 1000));
  const nonce = crypto.randomUUID();
  const signature = await signHmac(API_SIGNING_SECRET, `${timestamp}.${nonce}`);

  const response = await fetch(`${apiUrl.replace(/\/$/, '')}/auth/token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Api-Key': API_KEY,
      'X-Timestamp': timestamp,
      'X-Nonce': nonce,
      'X-Signature': signature,
    },
  });

  if (!response.ok) {
    throw new Error(`Auth failed: ${response.status}`);
  }

  const data = await response.json();
  return { token: data.token, ttl: data.ttl ?? 300 };
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Returns the Authorization header value for a data request.
 * Handles token caching and refresh automatically.
 *
 * @param {string} apiUrl - The base API URL
 * @returns {string|null} "Bearer <token>" or null if auth is disabled
 */
export async function getAuthHeader(apiUrl) {
  if (!isAuthEnabled()) return null;

  let token = getCachedToken();
  if (!token) {
    const result = await fetchToken(apiUrl);
    token = result.token;
    cacheToken(token, result.ttl);
  }

  return `Bearer ${token}`;
}
