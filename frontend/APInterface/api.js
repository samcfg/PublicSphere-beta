/**
 * All functions return standardized {data, meta, error} responses.
 * Pure functions - no classes, fully compatible with React hooks.
 */

const BASE_URL = '/api';

/**
 * Generic fetch wrapper with error handling
 * Detects rate limiting (429) and dispatches global event
 * @private
 */
async function apiFetch(url, options = {}) {
  try {
    const { headers: optionHeaders, ...restOptions } = options;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...optionHeaders,
      },
      ...restOptions,
    });

    // Check for rate limit (429 Too Many Requests)
    if (response.status === 429) {
      // Dispatch global event for rate limit modal
      window.dispatchEvent(new CustomEvent('api:ratelimit'));
    }

    const json = await response.json();

    // Backend already returns {data, meta, error} format
    return json;
  } catch (error) {
    // Network or parse errors
    return {
      data: null,
      meta: { timestamp: new Date().toISOString(), source: 'client' },
      error: error.message,
    };
  }
}

// ============================================================================
// GRAPH API - Claims, Sources, Connections
// ============================================================================

/**
 * Fetch all claims
 * GET /api/claims/
 */
export async function fetchClaims() {
  return apiFetch(`${BASE_URL}/claims/`);
}

/**
 * Create a new claim
 * POST /api/claims/
 * @param {string} token - Auth token
 * @param {Object} data - {content: string}
 */
export async function createClaim(token, data) {
  return apiFetch(`${BASE_URL}/claims/`, {
    method: 'POST',
    headers: { 'Authorization': `Token ${token}` },
    body: JSON.stringify(data),
  });
}

/**
 * Get connections for a specific claim
 * GET /api/claims/:id/
 */
export async function fetchClaimConnections(claimId) {
  return apiFetch(`${BASE_URL}/claims/${claimId}/`);
}

/**
 * Update claim properties
 * PATCH /api/claims/:id/
 * @param {string} claimId
 * @param {Object} data - Properties to update
 */
export async function updateClaim(claimId, data) {
  return apiFetch(`${BASE_URL}/claims/${claimId}/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

/**
 * Delete a claim
 * DELETE /api/claims/:id/
 * @param {string} token - Auth token
 */
export async function deleteClaim(token, claimId) {
  return apiFetch(`${BASE_URL}/claims/${claimId}/`, {
    method: 'DELETE',
    headers: { 'Authorization': `Token ${token}` },
  });
}

/**
 * Fetch all sources
 * GET /api/sources/
 */
export async function fetchSources() {
  return apiFetch(`${BASE_URL}/sources/`);
}

/**
 * Create a new source
 * POST /api/sources/
 * @param {string} token - Auth token
 * @param {Object} data - {url, title, author, publication_date, source_type, content}
 */
export async function createSource(token, data) {
  return apiFetch(`${BASE_URL}/sources/`, {
    method: 'POST',
    headers: { 'Authorization': `Token ${token}` },
    body: JSON.stringify(data),
  });
}

/**
 * Get connections for a specific source
 * GET /api/sources/:id/
 */
export async function fetchSourceConnections(sourceId) {
  return apiFetch(`${BASE_URL}/sources/${sourceId}/`);
}

/**
 * Update source properties
 * PATCH /api/sources/:id/
 */
export async function updateSource(sourceId, data) {
  return apiFetch(`${BASE_URL}/sources/${sourceId}/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

/**
 * Delete a source
 * DELETE /api/sources/:id/
 * @param {string} token - Auth token
 */
export async function deleteSource(token, sourceId) {
  return apiFetch(`${BASE_URL}/sources/${sourceId}/`, {
    method: 'DELETE',
    headers: { 'Authorization': `Token ${token}` },
  });
}

/**
 * Create a connection (single or compound)
 * POST /api/connections/
 * @param {string} token - Auth token
 * Single: {from_node_id, to_node_id, notes?, logic_type?, composite_id?}
 * Compound: {source_node_ids: [ids], target_node_id, logic_type, notes?, composite_id?}
 */
export async function createConnection(token, data) {
  return apiFetch(`${BASE_URL}/connections/`, {
    method: 'POST',
    headers: { 'Authorization': `Token ${token}` },
    body: JSON.stringify(data),
  });
}

/**
 * Update connection properties (individual or composite_id)
 * PATCH /api/connections/:id/
 */
export async function updateConnection(connectionId, data) {
  return apiFetch(`${BASE_URL}/connections/${connectionId}/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

/**
 * Delete connection (individual or composite_id)
 * DELETE /api/connections/:id/
 */
export async function deleteConnection(connectionId) {
  return apiFetch(`${BASE_URL}/connections/${connectionId}/`, {
    method: 'DELETE',
  });
}

/**
 * Fetch complete graph (claims, sources, edges)
 * GET /api/graph/
 */
export async function fetchGraphData() {
  return apiFetch(`${BASE_URL}/graph/`);
}

// ============================================================================
// USER API - Authentication, Profiles, Contributions
// ============================================================================

/**
 * Register new user
 * POST /api/users/register/
 * @param {Object} data - {username, email, password}
 */
export async function registerUser(data) {
  return apiFetch(`${BASE_URL}/users/register/`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Login user
 * POST /api/users/login/
 * @param {Object} data - {username, password}
 * @returns {data: {user, token}}
 */
export async function loginUser(data) {
  return apiFetch(`${BASE_URL}/users/login/`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Logout user
 * POST /api/users/logout/
 * @param {string} token - Auth token
 */
export async function logoutUser(token) {
  return apiFetch(`${BASE_URL}/users/logout/`, {
    method: 'POST',
    headers: { 'Authorization': `Token ${token}` },
  });
}

/**
 * Get authenticated user's profile
 * GET /api/users/profile/
 * @param {string} token - Auth token
 */
export async function fetchUserProfile(token) {
  return apiFetch(`${BASE_URL}/users/profile/`, {
    headers: { 'Authorization': `Token ${token}` },
  });
}

/**
 * Update authenticated user's profile
 * PUT /api/users/profile/
 * @param {string} token - Auth token
 * @param {Object} data - Profile fields to update
 */
export async function updateUserProfile(token, data) {
  return apiFetch(`${BASE_URL}/users/profile/`, {
    method: 'PUT',
    headers: { 'Authorization': `Token ${token}` },
    body: JSON.stringify(data),
  });
}

/**
 * Get public profile for any user
 * GET /api/users/profile/:username/
 */
export async function fetchPublicProfile(username) {
  return apiFetch(`${BASE_URL}/users/profile/${username}/`);
}

/**
 * Get authenticated user's contributions (counts only)
 * GET /api/users/contributions/
 * @param {string} token - Auth token
 */
export async function fetchUserContributions(token) {
  return apiFetch(`${BASE_URL}/users/contributions/`, {
    headers: { 'Authorization': `Token ${token}` },
  });
}

/**
 * Get authenticated user's contributions with full details
 * GET /api/users/contributions/list/
 * @param {string} token - Auth token
 * @returns {Object} {claims: [...], sources: [...], connections: [...]}
 */
export async function fetchUserContributionsList(token) {
  return apiFetch(`${BASE_URL}/users/contributions/list/`, {
    headers: { 'Authorization': `Token ${token}` },
  });
}

/**
 * Get authenticated user's social contributions (comments and ratings)
 * GET /api/social/contributions/
 * @param {string} token - Auth token
 * @returns {Object} {comments: [...], ratings: [...]}
 */
export async function fetchUserSocialContributions(token) {
  return apiFetch(`${BASE_URL}/social/contributions/`, {
    headers: { 'Authorization': `Token ${token}` },
  });
}

/**
 * Get attribution info for an entity
 * GET /api/users/attribution/:uuid/?type=claim|source|connection
 * @param {string} token - Optional auth token to compute is_own for anonymous attributions
 */
export async function fetchEntityAttribution(entityUuid, entityType, token = null) {
  const options = token ? { headers: { 'Authorization': `Token ${token}` } } : {};
  return apiFetch(`${BASE_URL}/users/attribution/${entityUuid}/?type=${entityType}`, options);
}

/**
 * Get complete user data export (GDPR)
 * GET /api/users/data/
 * @param {string} token - Auth token
 * @returns {Object} Complete user data including base info, profile, attributions, modifications, contributions
 */
export async function fetchUserDataExport(token) {
  return apiFetch(`${BASE_URL}/users/data/`, {
    headers: { 'Authorization': `Token ${token}` },
  });
}

/**
 * Toggle anonymity for user's contribution
 * POST /api/users/toggle-anonymity/
 * @param {string} token - Auth token
 * @param {Object} data - {entity_uuid, entity_type, version_number?}
 */
export async function toggleAnonymity(token, data) {
  return apiFetch(`${BASE_URL}/users/toggle-anonymity/`, {
    method: 'POST',
    headers: { 'Authorization': `Token ${token}` },
    body: JSON.stringify(data),
  });
}

/**
 * Toggle anonymity for user's social contribution (comment or rating)
 * POST /api/social/toggle-anonymity/
 * @param {string} token - Auth token
 * @param {Object} data - {entity_id: int, entity_type: 'comment'|'rating'}
 */
export async function toggleSocialAnonymity(token, data) {
  return apiFetch(`${BASE_URL}/social/toggle-anonymity/`, {
    method: 'POST',
    headers: { 'Authorization': `Token ${token}` },
    body: JSON.stringify(data),
  });
}

/**
 * Get leaderboard
 * GET /api/users/leaderboard/?limit=100
 */
export async function fetchLeaderboard(limit = 100) {
  return apiFetch(`${BASE_URL}/users/leaderboard/?limit=${limit}`);
}

/**
 * Get attributions for multiple entities in one batch request
 * POST /api/users/attributions/batch/
 * @param {Array} entities - [{uuid: string, type: 'claim'|'source'|'connection'}, ...]
 * @param {string} token - Optional auth token to compute is_own for anonymous attributions
 * @returns {Object} {uuid: {creator: {...}, editors: [...]}, ...}
 */
export async function fetchBatchAttributions(entities, token = null) {
  const options = {
    method: 'POST',
    body: JSON.stringify({ entities }),
  };
  if (token) {
    options.headers = { 'Authorization': `Token ${token}` };
  }
  return apiFetch(`${BASE_URL}/users/attributions/batch/`, options);
}

// ============================================================================
// SOCIAL API - Ratings, Comments, Moderation
// ============================================================================

/**
 * Create or update rating
 * POST /api/social/ratings/
 * @param {string} token - Auth token
 * @param {Object} data - {entity_uuid, entity_type, dimension, score}
 */
export async function rateEntity(token, data) {
  return apiFetch(`${BASE_URL}/social/ratings/`, {
    method: 'POST',
    headers: { 'Authorization': `Token ${token}` },
    body: JSON.stringify(data),
  });
}

/**
 * Get aggregated ratings for entity
 * GET /api/social/ratings/entity/?entity=uuid&dimension=confidence|relevance
 * @param {string} token - Optional auth token to get user's own rating
 */
export async function fetchEntityRatings(entityUuid, dimension = null, token = null) {
  const url = dimension
    ? `${BASE_URL}/social/ratings/entity/?entity=${entityUuid}&dimension=${dimension}`
    : `${BASE_URL}/social/ratings/entity/?entity=${entityUuid}`;
  const options = token ? { headers: { 'Authorization': `Token ${token}` } } : {};
  return apiFetch(url, options);
}

/**
 * Delete user's own rating
 * DELETE /api/social/ratings/delete/?entity=uuid&entity_type=type&dimension=dimension
 * @param {string} token - Auth token
 */
export async function deleteRating(token, entityUuid, entityType, dimension = null) {
  const url = dimension
    ? `${BASE_URL}/social/ratings/delete/?entity=${entityUuid}&entity_type=${entityType}&dimension=${dimension}`
    : `${BASE_URL}/social/ratings/delete/?entity=${entityUuid}&entity_type=${entityType}`;
  return apiFetch(url, {
    method: 'DELETE',
    headers: { 'Authorization': `Token ${token}` },
  });
}

/**
 * Create comment
 * POST /api/social/comments/
 * @param {string} token - Auth token
 * @param {Object} data - {entity_uuid, entity_type, content, parent_comment?}
 */
export async function createComment(token, data) {
  return apiFetch(`${BASE_URL}/social/comments/`, {
    method: 'POST',
    headers: { 'Authorization': `Token ${token}` },
    body: JSON.stringify(data),
  });
}

/**
 * Get comments for entity
 * GET /api/social/comments/entity/?entity=uuid&sort=timestamp|score
 * @param {string} token - Optional auth token to compute is_own for anonymous comments
 */
export async function fetchEntityComments(entityUuid, sort = null, token = null) {
  const url = sort
    ? `${BASE_URL}/social/comments/entity/?entity=${entityUuid}&sort=${sort}`
    : `${BASE_URL}/social/comments/entity/?entity=${entityUuid}`;
  const options = token ? { headers: { 'Authorization': `Token ${token}` } } : {};
  return apiFetch(url, options);
}

/**
 * Update comment content
 * PATCH /api/social/comments/:id/
 * @param {string} token - Auth token
 * @param {Object} data - {content}
 */
export async function updateComment(token, commentId, data) {
  return apiFetch(`${BASE_URL}/social/comments/${commentId}/`, {
    method: 'PATCH',
    headers: { 'Authorization': `Token ${token}` },
    body: JSON.stringify(data),
  });
}

/**
 * Delete comment (soft delete)
 * DELETE /api/social/comments/:id/
 * @param {string} token - Auth token
 */
export async function deleteComment(token, commentId) {
  return apiFetch(`${BASE_URL}/social/comments/${commentId}/`, {
    method: 'DELETE',
    headers: { 'Authorization': `Token ${token}` },
  });
}

/**
 * Flag entity for moderation (moderator only)
 * POST /api/social/moderation/flag/
 * @param {string} token - Auth token
 * @param {Object} data - {entity_uuid, entity_type, reason}
 */
export async function flagEntity(token, data) {
  return apiFetch(`${BASE_URL}/social/moderation/flag/`, {
    method: 'POST',
    headers: { 'Authorization': `Token ${token}` },
    body: JSON.stringify(data),
  });
}

/**
 * Get pending moderation flags (moderator only)
 * GET /api/social/moderation/flags/pending/
 * @param {string} token - Auth token
 */
export async function fetchPendingFlags(token) {
  return apiFetch(`${BASE_URL}/social/moderation/flags/pending/`, {
    headers: { 'Authorization': `Token ${token}` },
  });
}

/**
 * Resolve moderation flag (staff admin only)
 * POST /api/social/moderation/flags/:id/resolve/
 * @param {string} token - Auth token
 * @param {Object} data - {status: 'reviewed'|'action_taken'|'dismissed', resolution_notes?}
 */
export async function resolveFlag(token, flagId, data) {
  return apiFetch(`${BASE_URL}/social/moderation/flags/${flagId}/resolve/`, {
    method: 'POST',
    headers: { 'Authorization': `Token ${token}` },
    body: JSON.stringify(data),
  });
}

/**
 * Get controversial entities
 * GET /api/social/controversial/?limit=50
 */
export async function fetchControversialEntities(limit = 50) {
  return apiFetch(`${BASE_URL}/social/controversial/?limit=${limit}`);
}

// ============================================================================
// TEMPORAL API - Version History, Snapshots
// ============================================================================

/**
 * Get all versions for a claim
 * GET /api/temporal/claims/:node_id/versions/
 */
export async function fetchClaimVersions(nodeId) {
  return apiFetch(`${BASE_URL}/temporal/claims/${nodeId}/versions/`);
}

/**
 * Get all versions for a source
 * GET /api/temporal/sources/:node_id/versions/
 */
export async function fetchSourceVersions(nodeId) {
  return apiFetch(`${BASE_URL}/temporal/sources/${nodeId}/versions/`);
}

/**
 * Get all versions for a connection
 * GET /api/temporal/edges/:edge_id/versions/
 */
export async function fetchConnectionVersions(edgeId) {
  return apiFetch(`${BASE_URL}/temporal/edges/${edgeId}/versions/`);
}

/**
 * Get graph state at specific timestamp
 * GET /api/temporal/snapshot/?timestamp=ISO8601
 * @param {string} timestamp - ISO8601 timestamp
 */
export async function fetchGraphSnapshot(timestamp) {
  return apiFetch(`${BASE_URL}/temporal/snapshot/?timestamp=${encodeURIComponent(timestamp)}`);
}

/**
 * Get complete edit history for any entity
 * GET /api/temporal/history/?entity_uuid=uuid&entity_type=claim|source|connection
 */
export async function fetchEntityHistory(entityUuid, entityType) {
  return apiFetch(`${BASE_URL}/temporal/history/?entity_uuid=${entityUuid}&entity_type=${entityType}`);
}
