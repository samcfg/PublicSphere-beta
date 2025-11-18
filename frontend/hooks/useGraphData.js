/**
 * Custom React hook for fetching and managing graph data from DRF API.
 * Provides loading states, error handling, and data refresh functionality.
 * Also batch-fetches attributions for all entities to prevent rate limiting.
 */
import { useState, useEffect, useCallback } from 'react';
import { fetchGraphData, fetchBatchAttributions } from '../APInterface/api.js';

/**
 * Hook to fetch complete graph data (claims, sources, connections)
 * Also fetches attributions for all entities in batch
 * @returns {Object} {data, attributions, loading, error, refetch}
 */
export function useGraphData() {
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
    if (response.data?.elements) {
      response.data.elements.forEach(element => {
        if (element.data?.id && element.data?.type) {
          entities.push({
            uuid: element.data.id,
            type: element.data.type === 'claim' ? 'claim' :
                  element.data.type === 'source' ? 'source' :
                  element.data.label === 'Source' ? 'source' :
                  'connection'
          });
        }
      });
    }

    // Batch fetch attributions
    if (entities.length > 0) {
      const attrResponse = await fetchBatchAttributions(entities);
      if (!attrResponse.error && attrResponse.data) {
        setAttributions(attrResponse.data);
      }
    }

    setError(null);
    setLoading(false);
  }, []);

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
