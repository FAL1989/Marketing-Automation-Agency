import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { GenerationPreview } from '../../components/GenerationPreview';

describe('GenerationPreview', () => {
  const mockOnApprove = vi.fn();
  const mockOnEdit = vi.fn();
  const defaultProps = {
    content: 'Conteúdo gerado de teste',
    onApprove: mockOnApprove,
    onEdit: mockOnEdit
  };

  beforeEach(() => {
    mockOnApprove.mockClear();
    mockOnEdit.mockClear();
  });

  it('deve renderizar o conteúdo corretamente', () => {
    render(<GenerationPreview {...defaultProps} />);
    expect(screen.getByText('Conteúdo gerado de teste')).toBeInTheDocument();
  });

  it('deve chamar onApprove quando o botão de aprovar é clicado', () => {
    render(<GenerationPreview {...defaultProps} />);
    fireEvent.click(screen.getByText('Aprovar'));
    expect(mockOnApprove).toHaveBeenCalledTimes(1);
  });

  it('deve chamar onEdit quando o botão de editar é clicado', () => {
    render(<GenerationPreview {...defaultProps} />);
    fireEvent.click(screen.getByText('Editar'));
    expect(mockOnEdit).toHaveBeenCalledTimes(1);
  });

  it('deve renderizar o título da prévia', () => {
    render(<GenerationPreview {...defaultProps} />);
    expect(screen.getByText('Prévia do Conteúdo')).toBeInTheDocument();
  });

  it('deve renderizar os botões com os ícones corretos', () => {
    render(<GenerationPreview {...defaultProps} />);
    expect(screen.getByText('Editar').closest('button')).toHaveClass('bg-white');
    expect(screen.getByText('Aprovar').closest('button')).toHaveClass('bg-green-600');
  });
}); 