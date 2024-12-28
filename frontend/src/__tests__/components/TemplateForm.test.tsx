import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { TemplateForm } from '../../components/TemplateForm';
import { Template } from '../../types';

// Mock do ícone do Heroicons
vi.mock('@heroicons/react/24/solid', () => ({
  XMarkIcon: () => <span data-testid="close-icon">XMarkIcon</span>
}));

describe('TemplateForm', () => {
  const user = userEvent.setup({ delay: null });
  
  const mockTemplate: Template = {
    id: '1',
    name: 'Template de Teste',
    description: 'Descrição do template de teste',
    parameters: [],
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z'
  };

  const mockOnSubmit = vi.fn();
  const mockOnCancel = vi.fn();

  const renderTemplateForm = (template?: Template | null) => {
    return render(
      <TemplateForm
        template={template}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('deve renderizar o formulário vazio para novo template', () => {
    renderTemplateForm();
    
    expect(screen.getByText('Novo Template')).toBeInTheDocument();
    expect(screen.getByLabelText('Nome')).toHaveValue('');
    expect(screen.getByLabelText('Descrição')).toHaveValue('');
  });

  it('deve renderizar o formulário preenchido para edição', () => {
    renderTemplateForm(mockTemplate);
    
    expect(screen.getByText('Editar Template')).toBeInTheDocument();
    expect(screen.getByLabelText('Nome')).toHaveValue(mockTemplate.name);
    expect(screen.getByLabelText('Descrição')).toHaveValue(mockTemplate.description);
  });

  it('deve chamar onCancel ao clicar no botão de fechar', async () => {
    renderTemplateForm();
    
    const closeButton = screen.getByTestId('close-icon');
    await user.click(closeButton);
    
    await waitFor(() => {
      expect(mockOnCancel).toHaveBeenCalled();
    });
  });

  it('deve chamar onCancel ao clicar no botão cancelar', async () => {
    renderTemplateForm();
    
    const cancelButton = screen.getByText('Cancelar');
    await user.click(cancelButton);
    
    await waitFor(() => {
      expect(mockOnCancel).toHaveBeenCalled();
    });
  });

  it('deve atualizar os campos ao digitar', async () => {
    renderTemplateForm();
    
    const nameInput = screen.getByLabelText('Nome');
    const descriptionInput = screen.getByLabelText('Descrição');
    
    await user.type(nameInput, 'Novo Nome');
    await user.type(descriptionInput, 'Nova Descrição');
    
    await waitFor(() => {
      expect(nameInput).toHaveValue('Novo Nome');
      expect(descriptionInput).toHaveValue('Nova Descrição');
    });
  });

  it('deve chamar onSubmit com os dados corretos ao enviar o formulário', async () => {
    renderTemplateForm();
    
    const nameInput = screen.getByLabelText('Nome');
    const descriptionInput = screen.getByLabelText('Descrição');
    
    await user.type(nameInput, 'Novo Template');
    await user.type(descriptionInput, 'Descrição do novo template');
    
    const submitButton = screen.getByText('Salvar');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        name: 'Novo Template',
        description: 'Descrição do novo template',
        parameters: []
      });
    });
  });

  it('deve limpar o formulário após envio bem-sucedido', async () => {
    mockOnSubmit.mockResolvedValue(undefined);
    renderTemplateForm();
    
    const nameInput = screen.getByLabelText('Nome');
    const descriptionInput = screen.getByLabelText('Descrição');
    
    await user.type(nameInput, 'Novo Template');
    await user.type(descriptionInput, 'Descrição do novo template');
    
    const submitButton = screen.getByText('Salvar');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(nameInput).toHaveValue('');
      expect(descriptionInput).toHaveValue('');
    });
  });

  it('deve manter os dados no formulário se o envio falhar', async () => {
    mockOnSubmit.mockRejectedValue(new Error('Erro ao salvar'));
    renderTemplateForm();
    
    const nameInput = screen.getByLabelText('Nome');
    const descriptionInput = screen.getByLabelText('Descrição');
    
    await user.type(nameInput, 'Novo Template');
    await user.type(descriptionInput, 'Descrição do novo template');
    
    const submitButton = screen.getByText('Salvar');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(nameInput).toHaveValue('Novo Template');
      expect(descriptionInput).toHaveValue('Descrição do novo template');
    });
  });

  it('deve ter os estilos corretos nos elementos principais', () => {
    renderTemplateForm();
    
    // Verifica o container principal
    const overlay = screen.getByTestId('template-form-overlay');
    expect(overlay).toHaveClass('fixed', 'inset-0', 'bg-gray-500', 'bg-opacity-75', 'flex', 'items-center', 'justify-center', 'p-4');
    
    // Verifica o container do formulário
    const formContainer = screen.getByTestId('template-form-container');
    expect(formContainer).toHaveClass('bg-white', 'rounded-lg', 'shadow-xl', 'max-w-lg', 'w-full');
    
    // Verifica o cabeçalho
    const header = screen.getByTestId('template-form-header');
    expect(header).toHaveClass('flex', 'items-center', 'justify-between', 'p-4', 'border-b');
    
    // Verifica o formulário
    const form = screen.getByTestId('template-form');
    expect(form).toHaveClass('p-4', 'space-y-4');
    
    // Verifica os campos
    const nameInput = screen.getByLabelText('Nome');
    expect(nameInput).toHaveClass(
      'mt-1',
      'block',
      'w-full',
      'rounded-md',
      'border-gray-300',
      'shadow-sm',
      'focus:border-indigo-500',
      'focus:ring-indigo-500',
      'sm:text-sm'
    );
    
    const descriptionInput = screen.getByLabelText('Descrição');
    expect(descriptionInput).toHaveClass(
      'mt-1',
      'block',
      'w-full',
      'rounded-md',
      'border-gray-300',
      'shadow-sm',
      'focus:border-indigo-500',
      'focus:ring-indigo-500',
      'sm:text-sm'
    );
    
    // Verifica os botões
    const cancelButton = screen.getByRole('button', { name: /cancelar/i });
    expect(cancelButton).toHaveClass(
      'px-4',
      'py-2',
      'text-sm',
      'font-medium',
      'text-gray-700',
      'bg-white',
      'border',
      'border-gray-300',
      'rounded-md',
      'shadow-sm',
      'hover:bg-gray-50',
      'focus:outline-none',
      'focus:ring-2',
      'focus:ring-offset-2',
      'focus:ring-indigo-500'
    );
    
    const saveButton = screen.getByRole('button', { name: /salvar/i });
    expect(saveButton).toHaveClass(
      'px-4',
      'py-2',
      'text-sm',
      'font-medium',
      'text-white',
      'bg-indigo-600',
      'border',
      'border-transparent',
      'rounded-md',
      'shadow-sm',
      'hover:bg-indigo-700',
      'focus:outline-none',
      'focus:ring-2',
      'focus:ring-offset-2',
      'focus:ring-indigo-500'
    );
  });
}); 