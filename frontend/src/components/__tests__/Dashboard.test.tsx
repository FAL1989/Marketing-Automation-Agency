import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Dashboard } from '../Dashboard';
import { useAnalytics } from '../../hooks/useAnalytics';
import { useNotification } from '../../hooks/useNotification';

// Mock dos hooks
vi.mock('../../hooks/useAnalytics');
vi.mock('../../hooks/useNotification');

describe('Dashboard', () => {
  const mockMetrics = {
    totalGenerations: 1000,
    successRate: 95.5,
    averageTime: 2.3,
    activeTemplates: 15,
    recentGenerations: [
      {
        id: '1',
        templateId: 'template1',
        content: 'Geração 1',
        parameters: { param1: 'value1' },
        status: 'success',
        createdAt: '2024-03-20T10:00:00Z',
        updatedAt: '2024-03-20T10:00:00Z',
      },
    ],
    popularTemplates: [
      {
        templateId: 'template1',
        name: 'Template 1',
        usageCount: 50,
      },
    ],
  };

  const mockNotification = {
    showSuccess: vi.fn(),
    showError: vi.fn(),
    showWarning: vi.fn(),
    showInfo: vi.fn(),
    showNotification: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (useAnalytics as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      metrics: mockMetrics,
      isLoading: false,
      error: null,
      track: vi.fn(),
      refreshMetrics: vi.fn(),
    });
    (useNotification as unknown as ReturnType<typeof vi.fn>).mockReturnValue(mockNotification);
  });

  it('deve renderizar os cards de métricas corretamente', () => {
    render(<Dashboard />);

    expect(screen.getByText('Total de Gerações')).toBeInTheDocument();
    expect(screen.getByText('1,000')).toBeInTheDocument();
    expect(screen.getByText('Taxa de Sucesso')).toBeInTheDocument();
    expect(screen.getByText('95.5%')).toBeInTheDocument();
    expect(screen.getByText('Tempo Médio')).toBeInTheDocument();
    expect(screen.getByText('2.3s')).toBeInTheDocument();
    expect(screen.getByText('Templates Ativos')).toBeInTheDocument();
    expect(screen.getByText('15')).toBeInTheDocument();
  });

  it('deve exibir o estado de carregamento', () => {
    (useAnalytics as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      metrics: null,
      isLoading: true,
      error: null,
      track: vi.fn(),
      refreshMetrics: vi.fn(),
    });

    render(<Dashboard />);

    expect(screen.getByTestId('loading-state')).toBeInTheDocument();
  });

  it('deve exibir mensagem de erro quando houver falha', () => {
    const error = new Error('Falha ao carregar métricas');
    (useAnalytics as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      metrics: null,
      isLoading: false,
      error,
      track: vi.fn(),
      refreshMetrics: vi.fn(),
    });

    render(<Dashboard />);

    expect(screen.getByText(/Falha ao carregar métricas/i)).toBeInTheDocument();
  });

  it('deve atualizar métricas ao clicar no botão de atualização', async () => {
    const refreshMetrics = vi.fn();
    (useAnalytics as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      metrics: mockMetrics,
      isLoading: false,
      error: null,
      track: vi.fn(),
      refreshMetrics,
    });

    render(<Dashboard />);

    const refreshButton = screen.getByRole('button', { name: /atualizar/i });
    await fireEvent.click(refreshButton);

    expect(refreshMetrics).toHaveBeenCalled();
    expect(mockNotification.showInfo).toHaveBeenCalledWith('Atualizando métricas...');
  });

  it('deve exibir a lista de gerações recentes', () => {
    render(<Dashboard />);

    expect(screen.getByText('Geração 1')).toBeInTheDocument();
    expect(screen.getByText(/Template: Template 1/)).toBeInTheDocument();
  });

  it('deve filtrar gerações por status', () => {
    render(<Dashboard />);

    const filterSelect = screen.getByRole('combobox', { name: /filtrar por status/i });
    fireEvent.change(filterSelect, { target: { value: 'success' } });

    expect(screen.getByText('Geração 1')).toBeInTheDocument();
  });

  it('deve ordenar gerações por data', () => {
    render(<Dashboard />);

    const sortSelect = screen.getByRole('combobox', { name: /ordenar por/i });
    fireEvent.change(sortSelect, { target: { value: 'date-desc' } });

    expect(screen.getByText('Geração 1')).toBeInTheDocument();
  });

  it('deve exibir detalhes da geração ao clicar', () => {
    render(<Dashboard />);

    const generationItem = screen.getByText('Geração 1');
    fireEvent.click(generationItem);

    expect(screen.getByText(/parâmetros/i)).toBeInTheDocument();
    expect(screen.getByText('param1: value1')).toBeInTheDocument();
  });
}); 