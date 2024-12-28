import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { useAnalytics } from '../useAnalytics';
import { analyticsService } from '../../services/analyticsService';
import notificationsReducer from '../../store/slices/notificationsSlice';
import type { ReactNode } from 'react';

vi.mock('../../services/analyticsService');

describe('useAnalytics', () => {
  const mockStore = configureStore({
    reducer: {
      notifications: notificationsReducer
    }
  });

  const mockMetrics = {
    todayGenerations: 150,
    successRate: 95.5,
    avgGenerationTime: 2.3,
    generationTrend: 10,
    successTrend: 5,
    timeTrend: -2,
    dailyGenerations: [
      { date: '2024-03-19', count: 140 },
      { date: '2024-03-20', count: 150 }
    ],
    templateSuccess: [
      { templateId: '1', name: 'Template 1', successRate: 98 },
      { templateId: '2', name: 'Template 2', successRate: 92 }
    ],
    templateTimes: [
      { templateId: '1', name: 'Template 1', avgTime: 2.1 },
      { templateId: '2', name: 'Template 2', avgTime: 2.5 }
    ],
    errorDistribution: [
      { type: 'API Error', count: 10 },
      { type: 'Validation Error', count: 5 }
    ]
  };

  const wrapper = ({ children }: { children: ReactNode }) => (
    <Provider store={mockStore}>{children}</Provider>
  );

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('deve carregar métricas por intervalo de datas', async () => {
    vi.mocked(analyticsService.getMetricsByDateRange).mockResolvedValueOnce(mockMetrics);

    const { result } = renderHook(() => useAnalytics(), { wrapper });

    await act(async () => {
      await result.current.loadMetricsByDateRange('2024-03-19', '2024-03-20');
    });

    expect(result.current.metrics).toEqual(mockMetrics);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('deve carregar métricas por template', async () => {
    vi.mocked(analyticsService.getMetricsByTemplate).mockResolvedValueOnce(mockMetrics);

    const { result } = renderHook(() => useAnalytics(), { wrapper });

    await act(async () => {
      await result.current.loadMetricsByTemplate('1');
    });

    expect(result.current.metrics).toEqual(mockMetrics);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('deve lidar com erro ao carregar métricas', async () => {
    const error = new Error('Erro ao carregar métricas');
    vi.mocked(analyticsService.getMetricsByDateRange).mockRejectedValueOnce(error);

    const { result } = renderHook(() => useAnalytics(), { wrapper });

    await act(async () => {
      await result.current.loadMetricsByDateRange('2024-03-19', '2024-03-20');
    });

    expect(result.current.metrics).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBe(error.message);
  });
}); 