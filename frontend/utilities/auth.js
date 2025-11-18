/**
 * Low-level "api for browser's LocalStorage" 
 * Authentication utilities for token management and session handling.
 * Handles token storage, expiration, and automatic refresh logic.
 */

const TOKEN_KEY = 'ps_auth_token';
const EXPIRES_KEY = 'ps_token_expires';
const USER_KEY = 'ps_user';

// ============================================================================
// Token Storage
// ============================================================================

/**
 * Store authentication data after login/register
 * @param {string} token - Auth token
 * @param {string} expiresAt - ISO timestamp when token expires
 * @param {Object} user - User object
 */
export function storeAuth(token, expiresAt, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(EXPIRES_KEY, expiresAt);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

/**
 * Clear all authentication data
 */
export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(EXPIRES_KEY);
  localStorage.removeItem(USER_KEY);
}

/**
 * Get stored token
 * @returns {string|null}
 */
export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Get stored user object
 * @returns {Object|null}
 */
export function getUser() {
  const userStr = localStorage.getItem(USER_KEY);
  return userStr ? JSON.parse(userStr) : null;
}

// ============================================================================
// Token Expiration
// ============================================================================

/**
 * Check if current token is expired or close to expiring
 * @param {number} bufferMinutes - Minutes before expiration to consider "expired"
 * @returns {boolean}
 */
export function isTokenExpired(bufferMinutes = 0) {
  const expiresAt = localStorage.getItem(EXPIRES_KEY);
  if (!expiresAt) return true;

  const expirationTime = new Date(expiresAt).getTime();
  const now = Date.now();
  const buffer = bufferMinutes * 60 * 1000;

  return now >= (expirationTime - buffer);
}

/**
 * Get time remaining until token expires
 * @returns {number} Milliseconds remaining, or 0 if expired/missing
 */
export function getTimeUntilExpiration() {
  const expiresAt = localStorage.getItem(EXPIRES_KEY);
  if (!expiresAt) return 0;

  const remaining = new Date(expiresAt).getTime() - Date.now();
  return Math.max(0, remaining);
}

// ============================================================================
// Auth State
// ============================================================================

/**
 * Check if user is currently authenticated with valid token
 * @returns {boolean}
 */
export function isAuthenticated() {
  return !!getToken() && !isTokenExpired();
}

/**
 * Get auth headers for API requests
 * @returns {Object} Headers object with Authorization if authenticated
 */
export function getAuthHeaders() {
  const token = getToken();
  return token ? { 'Authorization': `Token ${token}` } : {};
}

// ============================================================================
// Session Management
// ============================================================================

/**
 * Handle authentication response from login/register
 * @param {Object} response - API response with {data: {token, expires_at, user}}
 * @returns {boolean} Success status
 */
export function handleAuthResponse(response) {
  if (response.data?.token && response.data?.expires_at && response.data?.user) {
    storeAuth(response.data.token, response.data.expires_at, response.data.user);
    return true;
  }
  return false;
}

/**
 * Handle logout - clears local storage and optionally calls backend
 * @param {Function} logoutApiFn - Optional async function to call backend logout
 */
export async function handleLogout(logoutApiFn = null) {
  const token = getToken();

  // Clear local state first (fail-fast for user)
  clearAuth();

  // Then attempt backend cleanup (don't block on this)
  if (logoutApiFn && token) {
    try {
      await logoutApiFn(token);
    } catch (err) {
      // Backend logout failed, but local state already cleared
      console.warn('Backend logout failed:', err);
    }
  }
}

/**
 * Check if 401 error indicates token expiration
 * @param {Object} response - API response object
 * @returns {boolean}
 */
export function isAuthError(response) {
  return response.error &&
         (response.error.includes('Token has expired') ||
          response.error.includes('Authentication') ||
          response.error.includes('Invalid token'));
}

// ============================================================================
// API Integration Helpers
// ============================================================================

/**
 * Wrapper to add auth headers to existing API functions
 * @param {Function} apiFn - API function from api.js
 * @param  {...any} args - Arguments to pass to API function
 * @returns {Promise<Object>} API response
 *
 * @example
 * const response = await withAuth(createClaim, {content: "My claim"});
 */
export async function withAuth(apiFn, ...args) {
  // Check expiration before making request
  if (isTokenExpired()) {
    return {
      data: null,
      meta: { timestamp: new Date().toISOString(), source: 'client' },
      error: 'Session expired. Please log in again.',
    };
  }

  // Call API function with original arguments
  const response = await apiFn(...args);

  // Check for auth errors in response
  if (isAuthError(response)) {
    clearAuth();
    // Could dispatch custom event here for global logout handling
    window.dispatchEvent(new CustomEvent('auth:expired'));
  }

  return response;
}
