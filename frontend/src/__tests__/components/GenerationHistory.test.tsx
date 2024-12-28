import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { GenerationHistory } from '../../components/GenerationHistory';
import { Generation } from '../../types';
import userEvent from '@testing-library/user-event';

// Mock dos ícones do Heroicons
vi.mock('@heroicons/react/24/outline', () => ({
  CheckCircleIcon: () => <div data-testid="check-circle-icon" />,
  XCircleIcon: () => <div data-testid="x-circle-icon" />,
  ClockIcon: () => <div data-testid="clock-icon" />
}));

// Mock da função de formatação de data
vi.mock('../../utils/dateUtils', () => ({
  formatDate: (date: string) => date
}));

describe('GenerationHistory', () => {
  const mockOnSelect = vi.fn();

  const mockGenerations: Generation[] = [
    {
      id: '1',
      content: 'Conteúdo 1 mais longo',
      status: 'success',
      createdAt: '2024-01-01T12:00:00',
      updatedAt: '2024-01-01T12:00:00',
      completedAt: '2024-01-01T12:00:00',
      templateId: '1',
      parameters: {}
    },
    {
      id: '2',
      content: 'Aguardando geração...',
      status: 'pending',
      createdAt: '2024-01-01T12:02:00',
      updatedAt: '2024-01-01T12:02:00',
      templateId: '1',
      parameters: {}
    },
    {
      id: '3',
      content: 'Conteúdo 3 mais longo',
      status: 'error',
      error: 'Erro na geração',
      createdAt: '2024-01-01T12:03:00',
      updatedAt: '2024-01-01T12:03:00',
      templateId: '1',
      parameters: {}
    }
  ];

  it('deve renderizar mensagem quando não há gerações', () => {
    render(<GenerationHistory generations={[]} onSelect={mockOnSelect} />);
    expect(screen.getByText('Nenhuma geração encontrada.')).toBeInTheDocument();
  });

  it('deve renderizar a lista de gerações com conteúdo truncado', () => {
    render(<GenerationHistory generations={mockGenerations} onSelect={mockOnSelect} />);

    expect(screen.getByText('Conteúdo 1...')).toBeInTheDocument();
    expect(screen.getByText('Aguardando geração...')).toBeInTheDocument();
    expect(screen.getByText('Conteúdo 3...')).toBeInTheDocument();
  });

  it('deve mostrar os status corretos para cada geração', () => {
    render(<GenerationHistory generations={mockGenerations} onSelect={mockOnSelect} />);

    expect(screen.getByText('Sucesso')).toBeInTheDocument();
    expect(screen.getByText('Em Progresso')).toBeInTheDocument();
    expect(screen.getByText('Erro')).toBeInTheDocument();
  });

  it('deve mostrar os ícones corretos para cada status', () => {
    render(<GenerationHistory generations={mockGenerations} onSelect={mockOnSelect} />);

    expect(screen.getByTestId('check-circle-icon')).toBeInTheDocument();
    expect(screen.getByTestId('clock-icon')).toBeInTheDocument();
    expect(screen.getByTestId('x-circle-icon')).toBeInTheDocument();
  });

  it('deve chamar onSelect quando uma geração é clicada', async () => {
    const user = userEvent.setup();
    render(<GenerationHistory generations={mockGenerations} onSelect={mockOnSelect} />);

    const generation = screen.getByText('Conteúdo 1...');
    await user.click(generation);

    expect(mockOnSelect).toHaveBeenCalledWith(mockGenerations[0]);
  });

  it('deve mostrar mensagem de erro quando presente', () => {
    render(<GenerationHistory generations={mockGenerations} onSelect={mockOnSelect} />);
    expect(screen.getByText('Erro na geração')).toBeInTheDocument();
  });

  it('deve mostrar a data para cada geração', () => {
    render(<GenerationHistory generations={mockGenerations} onSelect={mockOnSelect} />);

    expect(screen.getByText('2024-01-01T12:00:00')).toBeInTheDocument();
    expect(screen.getByText('2024-01-01T12:02:00')).toBeInTheDocument();
    expect(screen.getByText('2024-01-01T12:03:00')).toBeInTheDocument();
  });
}); 