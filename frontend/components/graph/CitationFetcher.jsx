import { useState } from 'react';

/**
 * Button to fetch citation metadata from URL using backend CitationFetcher
 *
 * Calls /api/graph/fetch-citation-metadata/ which wraps citation_fetcher.py
 * Returns structured metadata (authors, DOI, publication_date, etc.)
 *
 * @param {Object} props
 * @param {string} props.url - URL to fetch metadata from
 * @param {Function} props.onMetadataFetched - Callback: (metadata: Object) => void
 */
export function CitationFetcher({ url, onMetadataFetched }) {
  const [isFetching, setIsFetching] = useState(false);
  const [fetchError, setFetchError] = useState(null);

  const handleFetch = async () => {
    if (!url || !url.trim()) return;

    setIsFetching(true);
    setFetchError(null);

    try {
      const response = await fetch('/api/fetch-citation-metadata/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: url.trim() })
      });

      const result = await response.json();

      if (result.error) {
        setFetchError(result.error);
        return;
      }

      // Pass metadata to parent
      if (result.data?.metadata) {
        onMetadataFetched(result.data.metadata);
      }
    } catch (err) {
      console.error('Citation fetch failed:', err);
      setFetchError('Failed to fetch citation metadata');
    } finally {
      setIsFetching(false);
    }
  };

  return (
    <div style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'flex-end' }}>
      <button
        type="button"
        onClick={handleFetch}
        disabled={isFetching}
        style={{
          padding: '4px 8px',
          fontSize: '0.75rem',
          backgroundColor: 'var(--accent-blue)',
          color: 'var(--bg-secondary)',
          border: 'none',
          borderRadius: '4px',
          cursor: isFetching ? 'wait' : 'pointer',
          opacity: isFetching ? 0.6 : 1,
          whiteSpace: 'nowrap'
        }}
      >
        {isFetching ? 'Fetching...' : '↓ Fetch Metadata'}
      </button>
      {fetchError && (
        <span style={{
          fontSize: '0.7rem',
          color: '#ff4444',
          marginTop: '4px'
        }}>
          {fetchError}
        </span>
      )}
    </div>
  );
}
