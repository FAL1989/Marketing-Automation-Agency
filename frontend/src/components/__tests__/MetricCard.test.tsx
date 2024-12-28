import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { MetricCard } from '../../components/MetricCard';

describe('MetricCard', () => {
  const defaultProps = {
    title: 'Total de Gerações',
    value: '100',
    trend: 15,
    description: 'Gerações realizadas hoje',
    icon: 'chart-bar' as const
  };

  it('deve renderizar o título corretamente', () => {
    render(<MetricCard {...defaultProps} />);
    expect(screen.getByText('Total de Gerações')).toBeInTheDocument();
  });

  it('deve renderizar o valor corretamente', () => {
    render(<MetricCard {...defaultProps} />);
    expect(screen.getByText('100')).toBeInTheDocument();
  });

  it('deve renderizar a tendência positiva corretamente', () => {
    render(<MetricCard {...defaultProps} />);
    expect(screen.getByText('+15%')).toBeInTheDocument();
    expect(screen.getByTestId('trend-indicator')).toHaveClass('text-green-500');
  });

  it('deve renderizar a tendência negativa corretamente', () => {
    render(<MetricCard {...defaultProps} trend={-15} />);
    expect(screen.getByText('-15%')).toBeInTheDocument();
    expect(screen.getByTestId('trend-indicator')).toHaveClass('text-red-500');
  });

  it('deve renderizar a descrição quando fornecida', () => {
    render(<MetricCard {...defaultProps} />);
    expect(screen.getByText('Gerações realizadas hoje')).toBeInTheDocument();
  });

  it('não deve renderizar a descrição quando não fornecida', () => {
    render(<MetricCard {...defaultProps} description={undefined} />);
    expect(screen.queryByText('Gerações realizadas hoje')).not.toBeInTheDocument();
  });

  it('deve inverter a tendência quando trendInverted é true', () => {
    render(<MetricCard {...defaultProps} trend={15} trendInverted={true} />);
    expect(screen.getByText('+15%')).toBeInTheDocument();
    expect(screen.getByTestId('trend-indicator')).toHaveClass('text-red-500');
  });
}); 