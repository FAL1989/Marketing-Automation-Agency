import { describe, it, expect, vi, beforeEach } from 'vitest';
import { analyticsService } from '../analyticsService';
import { api } from '../api';

vi.mock('../api');

describe('analyticsService', () => {
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

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('deve obter métricas gerais', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockMetrics });

    const metrics = await analyticsService.getMetrics();

    expect(api.get).toHaveBeenCalledWith('/api/analytics/metrics');
    expect(metrics).toEqual(mockMetrics);
  });

  it('deve obter métricas por intervalo de datas', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockMetrics });

    const startDate = '2024-03-19';
    const endDate = '2024-03-20';
    const metrics = await analyticsService.getMetricsByDateRange(startDate, endDate);

    expect(api.get).toHaveBeenCalledWith('/api/analytics/metrics', {
      params: { startDate, endDate }
    });
    expect(metrics).toEqual(mockMetrics);
  });

  it('deve obter métricas por template', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockMetrics });

    const templateId = '1';
    const metrics = await analyticsService.getMetricsByTemplate(templateId);

    expect(api.get).toHaveBeenCalledWith(`/api/analytics/metrics/template/${templateId}`);
    expect(metrics).toEqual(mockMetrics);
  });

  it('deve lançar erro ao falhar em obter métricas gerais', async () => {
    const error = new Error('Erro ao obter métricas');
    vi.mocked(api.get).mockRejectedValueOnce(error);

    await expect(analyticsService.getMetrics()).rejects.toThrow(error);
  });

  it('deve lançar erro ao falhar em obter métricas por intervalo', async () => {
    const error = new Error('Erro ao obter métricas por intervalo');
    vi.mocked(api.get).mockRejectedValueOnce(error);

    await expect(analyticsService.getMetricsByDateRange('2024-03-19', '2024-03-20')).rejects.toThrow(error);
  });

  it('deve lançar erro ao falhar em obter métricas por template', async () => {
    const error = new Error('Erro ao obter métricas do template');
    vi.mocked(api.get).mockRejectedValueOnce(error);

    await expect(analyticsService.getMetricsByTemplate('1')).rejects.toThrow(error);
  });
}); 