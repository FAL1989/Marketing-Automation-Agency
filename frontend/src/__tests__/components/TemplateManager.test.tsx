import { render, screen, fireEvent } from '@testing-library/react';
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
    onCreateTemplate: vi.fn().mockResolvedValue({ id: '2', ...mockTemplates[0] }),
    onEditTemplate: vi.fn().mockResolvedValue({ ...mockTemplates[0], name: 'Template 1 (Editado)' }),
    onDeleteTemplate: vi.fn().mockResolvedValue(undefined),
    onSelectTemplate: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

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
    const template = screen.getByText('Template 1').closest('li');
    await userEvent.click(template!);
    expect(defaultProps.onSelectTemplate).toHaveBeenCalledWith(mockTemplates[0]);
  });

  it('deve chamar onDeleteTemplate ao clicar em excluir e confirmar', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockImplementation(() => true);
    render(<TemplateManager {...defaultProps} />);
    
    const deleteButton = screen.getByTestId('delete-button');
    await userEvent.click(deleteButton);
    
    expect(confirmSpy).toHaveBeenCalled();
    expect(defaultProps.onDeleteTemplate).toHaveBeenCalledWith('1');
  });

  it('não deve chamar onDeleteTemplate ao clicar em excluir e cancelar', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockImplementation(() => false);
    render(<TemplateManager {...defaultProps} />);
    
    const deleteButton = screen.getByTestId('delete-button');
    await userEvent.click(deleteButton);
    
    expect(confirmSpy).toHaveBeenCalled();
    expect(defaultProps.onDeleteTemplate).not.toHaveBeenCalled();
  });

  it('deve chamar onCreateTemplate ao clicar em Novo Template', async () => {
    render(<TemplateManager {...defaultProps} />);
    const newButton = screen.getByText('Novo Template');
    await userEvent.click(newButton);
    
    expect(defaultProps.onCreateTemplate).toHaveBeenCalledWith({
      name: 'Novo Template',
      description: 'Descrição do novo template',
      parameters: []
    });
  });

  it('deve chamar onEditTemplate ao clicar em editar template', async () => {
    render(<TemplateManager {...defaultProps} />);
    const editButton = screen.getByTestId('edit-button');
    await userEvent.click(editButton);
    
    expect(defaultProps.onEditTemplate).toHaveBeenCalledWith({
      ...mockTemplates[0],
      name: 'Template 1 (Editado)'
    });
  });
}); 