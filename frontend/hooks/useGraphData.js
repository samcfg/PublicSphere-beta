/**
 * Custom React hook for fetching and managing graph data from DRF API.
 * Provides loading states, error handling, and data refresh functionality.
 */
import { useState, useEffect, useCallback } from 'react';
import { fetchGraphData } from '../APInterface/api.js';

/**
 * Hook to fetch complete graph data (claims, sources, connections)
 * @returns {Object} {data, loading, error, refetch}
 */
export function useGraphData() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    const response = await fetchGraphData();

    if (response.error) {
      setError(response.error);
      setData(null);
    } else {
      setData(response.data);
      setError(null);
    }

    setLoading(false);
  }, []);

  // Fetch on mount
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    loading,
    error,
    refetch: fetchData, // Allow manual refresh
  };
}
