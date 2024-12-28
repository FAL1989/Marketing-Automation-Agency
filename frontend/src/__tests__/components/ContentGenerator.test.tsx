import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ContentGenerator } from '../../components/ContentGenerator';
import { Template, Variable } from '../../types';

const mockGenerateContent = vi.fn();
const mockTemplate: Template = {
  id: '1',
  name: 'Template de Teste',
  description: 'Descrição do template',
  prompt: 'Prompt do template',
  parameters: [],
  variables: [
    { name: 'var1', type: 'text' } as Variable
  ],
  validationRules: [],
  versions: [],
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  createdBy: 'test-user',
  isPublic: false
};

vi.mock('../../hooks/useTemplate', () => ({
  useTemplate: () => ({
    template: mockTemplate,
    generateContent: mockGenerateContent,
    loading: false,
    error: null
  })
}));

describe('ContentGenerator', () => {
  it('deve gerar conteúdo quando o formulário é submetido', async () => {
    const user = userEvent.setup();
    render(<ContentGenerator template={mockTemplate} onGenerate={mockGenerateContent} />);

    const input = screen.getByLabelText('var1') as HTMLInputElement;
    await user.type(input, 'valor1');

    const submitButton = screen.getByRole('button', { name: /gerar conteúdo/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockGenerateContent).toHaveBeenCalledWith({
        templateId: '1',
        variables: { var1: 'valor1' }
      });
    });
  });

  it('deve desabilitar o botão durante o carregamento', async () => {
    render(<ContentGenerator template={mockTemplate} onGenerate={mockGenerateContent} isLoading={true} />);

    const submitButton = screen.getByRole('button');
    expect(submitButton).toBeDisabled();
    expect(submitButton).toHaveTextContent('Gerando...');
  });

  it('deve mostrar mensagem de erro quando a geração falha', async () => {
    render(<ContentGenerator template={mockTemplate} onGenerate={mockGenerateContent} error="Erro ao gerar conteúdo" />);

    const errorAlert = screen.getByRole('alert');
    expect(errorAlert).toHaveTextContent('Erro ao gerar conteúdo');
  });
}); 