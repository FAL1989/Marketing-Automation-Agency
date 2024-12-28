import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { TemplateManager } from '../../components/TemplateManager';
import userEvent from '@testing-library/user-event';

describe('TemplateManager', () => {
  const mockTemplates = [
    {
      id: '1',
      name: 'Template 1',
      description: 'Descrição do template 1',
      parameters: [],
      createdAt: '2023-01-01',
      updatedAt: '2023-01-01',
    },
  ];

  const defaultProps = {
    templates: mockTemplates,
    onCreateTemplate: vi.fn(),
    onEditTemplate: vi.fn(),
    onDeleteTemplate: vi.fn(),
    onSelectTemplate: vi.fn(),
  };

  it('deve renderizar a lista de templates', () => {
    render(<TemplateManager {...defaultProps} />);
    expect(screen.getByText('Template 1')).toBeInTheDocument();
    expect(screen.getByText('Descrição do template 1')).toBeInTheDocument();
  });

  it('deve mostrar mensagem quando não há templates', () => {
    render(<TemplateManager {...defaultProps} templates={[]} />);
    expect(screen.getByText(/nenhum template encontrado/i)).toBeInTheDocument();
  });

  it('deve chamar onSelectTemplate ao clicar em um template', async () => {
    render(<TemplateManager {...defaultProps} />);
    await userEvent.click(screen.getByText('Template 1'));
    expect(defaultProps.onSelectTemplate).toHaveBeenCalledWith(mockTemplates[0]);
  });

  it('deve chamar onDeleteTemplate ao clicar em excluir e confirmar', async () => {
    vi.spyOn(window, 'confirm').mockImplementation(() => true);
    render(<TemplateManager {...defaultProps} />);
    await userEvent.click(screen.getByTestId('delete-button'));
    expect(defaultProps.onDeleteTemplate).toHaveBeenCalledWith('1');
  });

  it('não deve chamar onDeleteTemplate ao clicar em excluir e cancelar', async () => {
    vi.spyOn(window, 'confirm').mockImplementation(() => false);
    render(<TemplateManager {...defaultProps} />);
    await userEvent.click(screen.getByTestId('delete-button'));
    expect(defaultProps.onDeleteTemplate).not.toHaveBeenCalled();
  });

  it('deve chamar onCreateTemplate ao clicar em Novo Template', async () => {
    render(<TemplateManager {...defaultProps} />);
    await userEvent.click(screen.getByText('Novo Template'));
    expect(defaultProps.onCreateTemplate).toHaveBeenCalled();
  });

  it('deve chamar onEditTemplate ao clicar em editar template', async () => {
    render(<TemplateManager {...defaultProps} />);
    await userEvent.click(screen.getByTestId('edit-button'));
    expect(defaultProps.onEditTemplate).toHaveBeenCalled();
  });
}); 