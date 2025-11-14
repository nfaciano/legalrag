import { useAuth } from '@clerk/clerk-react';
import { useMemo } from 'react';
import { ApiClient } from './api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export function useApi() {
  const { getToken } = useAuth();

  const apiClient = useMemo(() => {
    return new ApiClient(API_BASE_URL, getToken);
  }, [getToken]);

  return apiClient;
}
