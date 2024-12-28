import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { TemplateEditorModal } from '../../components/TemplateEditorModal';
import { Template } from '../../types';

// Mock dos ícones do Heroicons
vi.mock('@heroicons/react/24/outline', () => ({
  XMarkIcon: () => <span data-testid="close-icon">XMarkIcon</span>
}));

// Mock do componente TemplateEditor
vi.mock('../../components/TemplateEditor', () => ({
  TemplateEditor: ({ template, onSave, onCancel }: { 
    template: Template | null, 
    onSave: (template: Template) => Promise<void>,
    onCancel: () => void 
  }) => (
    <div data-testid="template-editor">
      <div className="basic-info">
        <input
          type="text"
          value={template?.name || ''}
          onChange={(e) => onSave({ ...template!, name: e.target.value })}
        />
        <button type="button" onClick={() => onSave(template!)}>Salvar</button>
        <button type="button" onClick={onCancel}>Cancelar</button>
      </div>
    </div>
  )
}));

describe('TemplateEditorModal', () => {
  const mockTemplate: Template = {
    id: '1',
    name: 'Template de Teste',
    description: 'Descrição do template de teste',
    prompt: 'Prompt do template',
    variables: [],
    validationRules: [],
    parameters: [],
    versions: [],
    createdAt: '2024-01-01T00:00:00.000Z',
    updatedAt: '2024-01-01T00:00:00.000Z',
    createdBy: 'test-user',
    isPublic: false
  };

  const mockOnClose = vi.fn();
  const mockOnSave = vi.fn();

  const renderModal = (template: Template | null = null, isOpen: boolean = true) => {
    return render(
      <TemplateEditorModal
        isOpen={isOpen}
        onClose={mockOnClose}
        template={template}
        onSave={mockOnSave}
      />
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('deve renderizar o modal quando isOpen é true', () => {
    renderModal();
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('deve mostrar título correto para novo template', () => {
    renderModal(null);
    expect(screen.getByText('Novo Template')).toBeInTheDocument();
  });

  it('deve mostrar título correto para edição de template', () => {
    renderModal(mockTemplate);
    expect(screen.getByText('Editar Template')).toBeInTheDocument();
  });

  it('deve chamar onClose ao clicar no botão de fechar', async () => {
    renderModal();
    
    const closeButton = screen.getByTestId('close-icon');
    await userEvent.click(closeButton);
    
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('deve renderizar o TemplateEditor com as props corretas', () => {
    renderModal(mockTemplate);
    expect(screen.getByTestId('template-editor')).toBeInTheDocument();
  });

  it('deve chamar onSave e onClose quando o template é salvo', async () => {
    mockOnSave.mockResolvedValue(undefined);
    renderModal(mockTemplate);
    
    const saveButton = screen.getByText('Salvar');
    await userEvent.click(saveButton);
    
    const expectedTemplate = {
      ...mockTemplate,
      updatedAt: expect.any(String)
    };
    
    expect(mockOnSave).toHaveBeenCalledWith(expectedTemplate);
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('deve chamar onClose quando o editor é cancelado', async () => {
    renderModal();
    
    const cancelButton = screen.getByText('Cancelar');
    await userEvent.click(cancelButton);
    
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('deve ter os estilos corretos nos elementos principais', () => {
    renderModal();
    
    // Verifica o overlay
    const overlay = screen.getByTestId('modal-overlay');
    expect(overlay).toHaveClass('fixed', 'inset-0', 'bg-black/30');
    
    // Verifica o container do modal
    const modalContainer = screen.getByTestId('modal-container');
    expect(modalContainer).toHaveClass('fixed', 'inset-0', 'flex', 'items-center', 'justify-center');
    
    // Verifica o painel do modal
    const modalPanel = screen.getByTestId('modal-panel');
    expect(modalPanel).toHaveClass('mx-auto', 'max-w-3xl', 'w-full', 'bg-white', 'rounded-lg', 'shadow-xl');
  });

  it('deve ter a estrutura correta do cabeçalho', () => {
    renderModal();
    
    const header = screen.getByText('Novo Template').parentElement;
    expect(header).toHaveClass('flex', 'items-center', 'justify-between', 'p-4', 'border-b');
    
    const title = screen.getByText('Novo Template');
    expect(title).toHaveClass('text-lg', 'font-medium', 'text-gray-900');
    
    const closeButton = screen.getByTestId('close-icon').parentElement;
    expect(closeButton).toHaveClass('text-gray-400', 'hover:text-gray-500');
  });
}); 