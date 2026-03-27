import { useState, useEffect, useCallback } from 'react';

export function useApi(fetchFn, params = null, autoFetch = true) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(autoFetch);
  const [error, setError] = useState(null);

  const execute = useCallback(async (overrideParams) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchFn(overrideParams || params);
      setData(result);
      return result;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, [fetchFn, params]);

  useEffect(() => {
    if (autoFetch) execute();
  }, []);

  return { data, loading, error, execute };
}

export function usePolling(fetchFn, intervalMs = 60000) {
  const { data, loading, error, execute } = useApi(fetchFn, null, true);

  useEffect(() => {
    const id = setInterval(execute, intervalMs);
    return () => clearInterval(id);
  }, [execute, intervalMs]);

  return { data, loading, error, refresh: execute };
}
