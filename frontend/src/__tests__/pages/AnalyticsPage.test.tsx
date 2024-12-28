import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { AnalyticsPage } from '../../pages/AnalyticsPage';
import { analyticsService } from '../../services/analyticsService';
import notificationsReducer from '../../store/slices/notificationsSlice';

vi.mock('../../services/analyticsService');

describe('AnalyticsPage', () => {
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

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('deve renderizar o título da página', () => {
    vi.mocked(analyticsService.getMetricsByDateRange).mockResolvedValueOnce(mockMetrics);

    render(
      <Provider store={mockStore}>
        <AnalyticsPage />
      </Provider>
    );

    expect(screen.getByText('Métricas Avançadas')).toBeInTheDocument();
  });

  it('deve carregar e exibir as métricas', async () => {
    vi.mocked(analyticsService.getMetricsByDateRange).mockResolvedValueOnce(mockMetrics);

    render(
      <Provider store={mockStore}>
        <AnalyticsPage />
      </Provider>
    );

    await waitFor(() => {
      expect(screen.getByText('150')).toBeInTheDocument(); // todayGenerations
      expect(screen.getByText('95.5%')).toBeInTheDocument(); // successRate
      expect(screen.getByText('2.3s')).toBeInTheDocument(); // avgGenerationTime
    });
  });

  it('deve exibir mensagem de erro ao falhar em carregar métricas', async () => {
    const error = new Error('Erro ao carregar métricas');
    vi.mocked(analyticsService.getMetricsByDateRange).mockRejectedValueOnce(error);

    render(
      <Provider store={mockStore}>
        <AnalyticsPage />
      </Provider>
    );

    await waitFor(() => {
      expect(screen.getByText(error.message)).toBeInTheDocument();
    });
  });
}); 