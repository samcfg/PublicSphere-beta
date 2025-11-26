/**
 * Custom React hook for fetching and managing graph data from DRF API.
 * Provides loading states, error handling, and data refresh functionality.
 * Also batch-fetches attributions for all entities to prevent rate limiting.
 */
import { useState, useEffect, useCallback } from 'react';
import { fetchGraphData, fetchBatchAttributions } from '../APInterface/api.js';
import { useAuth } from '../utilities/AuthContext.jsx';

/**
 * Hook to fetch complete graph data (claims, sources, connections)
 * Also fetches attributions for all entities in batch
 * @returns {Object} {data, attributions, loading, error, refetch}
 */
export function useGraphData() {
  const { token } = useAuth();
  const [data, setData] = useState(null);
  const [attributions, setAttributions] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    const response = await fetchGraphData();

    if (response.error) {
      setError(response.error);
      setData(null);
      setAttributions({});
      setLoading(false);
      return;
    }

    setData(response.data);

    // Extract all entity UUIDs from graph data
    const entities = [];

    // Add claims - structure is { claim: { properties: { id: "uuid" } } }
    if (response.data?.claims) {
      response.data.claims.forEach(item => {
        const uuid = item?.claim?.properties?.id;
        if (uuid) {
          entities.push({ uuid, type: 'claim' });
        }
      });
    }

    // Add sources - structure is { source: { properties: { id: "uuid" } } }
    if (response.data?.sources) {
      response.data.sources.forEach(item => {
        const uuid = item?.source?.properties?.id;
        if (uuid) {
          entities.push({ uuid, type: 'source' });
        }
      });
    }

    // Add edges - structure is { connection: { properties: { id: "uuid" } } }
    if (response.data?.edges) {
      response.data.edges.forEach(item => {
        const uuid = item?.connection?.properties?.id;
        if (uuid) {
          entities.push({ uuid, type: 'connection' });
        }
      });
    }

    // Batch fetch attributions
    if (entities.length > 0) {
      const attrResponse = await fetchBatchAttributions(entities, token);

      // Handle both wrapped and unwrapped response formats
      const attributionData = attrResponse.data || attrResponse;

      if (!attrResponse.error && attributionData && typeof attributionData === 'object') {
        setAttributions(attributionData);
      }
    }

    setError(null);
    setLoading(false);
  }, [token]);

  // Fetch on mount
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    attributions,
    loading,
    error,
    refetch: fetchData, // Allow manual refresh
  };
}
