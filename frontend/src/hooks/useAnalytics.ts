import { useState } from 'react';
import * as analyticsService from '../services/analyticsService';
import type { AnalyticsData } from '../types';

export const useAnalytics = () => {
  const [metrics, setMetrics] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = async (
    fetcher: () => Promise<any>,
    errorMessage = 'Failed to load metrics'
  ) => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await fetcher();
      setMetrics(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return {
    metrics,
    isLoading,
    error,
    loadMetrics: () => fetchMetrics(analyticsService.getMetrics),
    loadMetricsByDateRange: (startDate: string, endDate: string) =>
      fetchMetrics(() => analyticsService.getMetricsByDateRange(startDate, endDate)),
    loadMetricsByTemplate: (templateId: string) =>
      fetchMetrics(() => analyticsService.getMetricsByTemplate(templateId)),
    trackEvent: analyticsService.trackEvent,
  };
}; 