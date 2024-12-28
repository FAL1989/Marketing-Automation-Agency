import { renderHook, act, waitFor } from '@testing-library/react';
import { useAnalytics } from '../useAnalytics';
import { getMetrics, trackEvent } from '../../services/analyticsService';
import { vi } from 'vitest';

vi.mock('../../services/analyticsService', () => ({
  getMetrics: vi.fn(),
  trackEvent: vi.fn(),
}));

describe('useAnalytics', () => {
  const mockMetrics = {
    totalGenerations: 100,
    successRate: 95.5,
    averageTime: 2.3,
    activeTemplates: 10,
    recentGenerations: [],
    popularTemplates: [],
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('deve buscar métricas ao montar o componente', async () => {
    (getMetrics as jest.Mock).mockResolvedValueOnce(mockMetrics);

    const { result } = renderHook(() => useAnalytics());

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.metrics).toEqual(mockMetrics);
    expect(getMetrics).toHaveBeenCalled();
  });

  it('deve atualizar o estado de loading corretamente', async () => {
    (getMetrics as jest.Mock).mockResolvedValueOnce(mockMetrics);

    const { result } = renderHook(() => useAnalytics());

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.metrics).toEqual(mockMetrics);
  });

  it('deve lidar com erros ao buscar métricas', async () => {
    const error = new Error('Falha ao buscar métricas');
    (getMetrics as jest.Mock).mockRejectedValueOnce(error);

    const { result } = renderHook(() => useAnalytics());

    await waitFor(() => {
      expect(result.current.error).toBe(error);
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.metrics).toBeNull();
  });

  it('deve rastrear eventos corretamente', async () => {
    const { result } = renderHook(() => useAnalytics());
    const eventName = 'test_event';
    const eventData = { key: 'value' };

    await act(async () => {
      await result.current.track(eventName, eventData);
    });

    expect(trackEvent).toHaveBeenCalledWith(eventName, eventData);
  });

  it('deve atualizar métricas manualmente', async () => {
    const updatedMetrics = { ...mockMetrics, totalGenerations: 150 };
    (getMetrics as jest.Mock)
      .mockResolvedValueOnce(mockMetrics)
      .mockResolvedValueOnce(updatedMetrics);

    const { result } = renderHook(() => useAnalytics());

    await waitFor(() => {
      expect(result.current.metrics).toEqual(mockMetrics);
    });

    await act(async () => {
      await result.current.refreshMetrics();
    });

    expect(result.current.metrics).toEqual(updatedMetrics);
    expect(getMetrics).toHaveBeenCalledTimes(2);
  });

  it('deve lidar com erros ao rastrear eventos', async () => {
    const error = new Error('Falha ao rastrear evento');
    (trackEvent as jest.Mock).mockRejectedValueOnce(error);

    const { result } = renderHook(() => useAnalytics());
    const eventName = 'test_event';
    const eventData = { key: 'value' };

    await expect(result.current.track(eventName, eventData)).rejects.toThrow(error);
  });
}); 