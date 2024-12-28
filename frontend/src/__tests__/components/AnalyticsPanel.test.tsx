import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AnalyticsPanel } from '../../components/AnalyticsPanel';
import { api } from '../../services/api';

// Mock do módulo chart.js
vi.mock('chart.js', () => ({
  Chart: {
    register: vi.fn()
  },
  CategoryScale: vi.fn(),
  LinearScale: vi.fn(),
  PointElement: vi.fn(),
  LineElement: vi.fn(),
  BarElement: vi.fn(),
  ArcElement: vi.fn(),
  Title: vi.fn(),
  Tooltip: vi.fn(),
  Legend: vi.fn()
}));

// Mock dos componentes do react-chartjs-2
vi.mock('react-chartjs-2', () => ({
  Line: () => <div data-testid="line-chart">Line Chart</div>,
  Bar: () => <div data-testid="bar-chart">Bar Chart</div>,
  Pie: () => <div data-testid="pie-chart">Pie Chart</div>
}));

// Mock do serviço de API
vi.mock('../../services/api', () => ({
  api: {
    get: vi.fn()
  }
}));

describe('AnalyticsPanel', () => {
  const mockChartData = {
    labels: ['Jan', 'Fev', 'Mar'],
    datasets: [
      {
        label: 'Dados',
        data: [10, 20, 30],
        backgroundColor: 'rgba(99, 102, 241, 0.5)',
        borderColor: 'rgb(99, 102, 241)'
      }
    ]
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('deve mostrar o loading state inicialmente', () => {
    render(
      <AnalyticsPanel
        title="Gráfico de Teste"
        type="line"
        timeRange="week"
      />
    );

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('deve renderizar o gráfico de linha quando type="line"', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockChartData });

    render(
      <AnalyticsPanel
        title="Gráfico de Linha"
        type="line"
        timeRange="week"
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });
  });

  it('deve renderizar o gráfico de barras quando type="bar"', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockChartData });

    render(
      <AnalyticsPanel
        title="Gráfico de Barras"
        type="bar"
        timeRange="week"
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
    });
  });

  it('deve renderizar o gráfico de pizza quando type="pie"', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockChartData });

    render(
      <AnalyticsPanel
        title="Gráfico de Pizza"
        type="pie"
        timeRange="week"
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
    });
  });

  it('deve mostrar mensagem de erro quando a requisição falha', async () => {
    vi.mocked(api.get).mockRejectedValueOnce(new Error('Erro ao carregar dados'));

    render(
      <AnalyticsPanel
        title="Gráfico com Erro"
        type="line"
        timeRange="week"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Erro ao carregar dados do gráfico')).toBeInTheDocument();
    });
  });

  it('deve chamar a API com os parâmetros corretos', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockChartData });

    render(
      <AnalyticsPanel
        title="Gráfico de Teste"
        type="line"
        timeRange="week"
      />
    );

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/analytics/chart/line', {
        params: { timeRange: 'week' }
      });
    });
  });

  it('deve atualizar os dados quando timeRange muda', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockChartData });

    const { rerender } = render(
      <AnalyticsPanel
        title="Gráfico de Teste"
        type="line"
        timeRange="week"
      />
    );

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/analytics/chart/line', {
        params: { timeRange: 'week' }
      });
    });

    vi.mocked(api.get).mockResolvedValueOnce({ data: mockChartData });

    rerender(
      <AnalyticsPanel
        title="Gráfico de Teste"
        type="line"
        timeRange="month"
      />
    );

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/analytics/chart/line', {
        params: { timeRange: 'month' }
      });
    });
  });
}); 