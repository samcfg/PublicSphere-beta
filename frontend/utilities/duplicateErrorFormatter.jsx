/**
 * Formats duplicate detection errors into rich JSX components
 * Used by both NodeCreationModal and StandaloneNodeCreationModal
 */

/**
 * Format a duplicate error response into a rich error display
 *
 * @param {string} errorType - Error code from API ('duplicate_exact', 'duplicate_similar', etc.)
 * @param {Object} data - Error data from API response
 * @param {string} nodeType - 'claim' or 'source'
 * @returns {JSX.Element|null} Formatted error component or null
 */
export function formatDuplicateError(errorType, data, nodeType = 'claim') {
  // Claim duplicate errors
  if (errorType === 'duplicate_exact' || errorType === 'duplicate_similar') {
    const label = errorType === 'duplicate_exact'
      ? `This ${nodeType} already exists`
      : `This ${nodeType} is very similar to an existing one`;

    const content = nodeType === 'claim'
      ? data?.existing_content
      : data?.existing_title;

    const existingId = data?.existing_node_id;
    const similarity = data?.similarity_score;

    return (
      <div className="duplicate-error">
        <strong>{label}</strong>
        <p style={{ fontStyle: 'italic', margin: '8px 0', fontSize: '14px' }}>
          {content?.slice(0, 150)}{content && content.length > 150 ? '...' : ''}
        </p>
        {similarity && (
          <small style={{ opacity: 0.7 }}>
            Similarity: {(similarity * 100).toFixed(0)}%
          </small>
        )}
        {existingId && (
          <a
            href={`/context?id=${existingId}`}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              color: 'var(--accent-blue)',
              textDecoration: 'underline',
              display: 'block',
              marginTop: '8px'
            }}
          >
            View existing {nodeType} →
          </a>
        )}
      </div>
    );
  }

  // Source URL duplicate
  if (errorType === 'duplicate_url') {
    const existingTitle = data?.existing_title || 'Unknown';
    const existingId = data?.existing_node_id;

    return (
      <div className="duplicate-error">
        <strong>This URL already exists</strong>
        <p style={{ fontStyle: 'italic', margin: '8px 0' }}>{existingTitle}</p>
        {existingId && (
          <a
            href={`/context?id=${existingId}`}
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: 'var(--accent-blue)', textDecoration: 'underline' }}
          >
            View existing source →
          </a>
        )}
      </div>
    );
  }

  // Source title duplicates
  if (errorType === 'duplicate_title_exact' || errorType === 'duplicate_title_similar') {
    const label = errorType === 'duplicate_title_exact'
      ? 'A source with this title already exists'
      : 'A source with a very similar title exists';

    const existingTitle = data?.existing_title || 'Unknown';
    const existingId = data?.existing_node_id;
    const similarity = data?.similarity_score;

    return (
      <div className="duplicate-error">
        <strong>{label}</strong>
        <p style={{ fontStyle: 'italic', margin: '8px 0' }}>{existingTitle}</p>
        {similarity && (
          <small style={{ opacity: 0.7 }}>
            Similarity: {(similarity * 100).toFixed(0)}%
          </small>
        )}
        {existingId && (
          <a
            href={`/context?id=${existingId}`}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              color: 'var(--accent-blue)',
              textDecoration: 'underline',
              display: 'block',
              marginTop: '8px'
            }}
          >
            View existing source →
          </a>
        )}
      </div>
    );
  }

  return null;
}
