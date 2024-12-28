import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { AdvancedMetrics } from '../../components/AdvancedMetrics';

describe('AdvancedMetrics', () => {
  const mockData = {
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

  it('deve renderizar os cards de métricas principais', () => {
    render(<AdvancedMetrics data={mockData} />);

    expect(screen.getByText('Gerações Hoje')).toBeInTheDocument();
    expect(screen.getByText('150')).toBeInTheDocument();
    expect(screen.getByText('Taxa de Sucesso')).toBeInTheDocument();
    expect(screen.getByText('95.5%')).toBeInTheDocument();
    expect(screen.getByText('Tempo Médio')).toBeInTheDocument();
    expect(screen.getByText('2.3s')).toBeInTheDocument();
  });

  it('deve renderizar os gráficos', () => {
    render(<AdvancedMetrics data={mockData} />);

    expect(screen.getByText('Gerações Diárias')).toBeInTheDocument();
    expect(screen.getByText('Taxa de Sucesso por Template')).toBeInTheDocument();
    expect(screen.getByText('Tempo Médio por Template')).toBeInTheDocument();
    expect(screen.getByText('Distribuição de Erros')).toBeInTheDocument();
  });

  it('deve exibir loading state', () => {
    render(<AdvancedMetrics data={mockData} isLoading={true} />);

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('deve exibir mensagem de erro', () => {
    const error = 'Erro ao carregar métricas';
    render(<AdvancedMetrics data={mockData} error={error} />);

    expect(screen.getByText(error)).toBeInTheDocument();
  });
}); 