import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { TemplateEditor } from '../../components/TemplateEditor';
import { Template } from '../../types/Template';
import userEvent from '@testing-library/user-event';
import { useTemplate } from '../../hooks/useTemplate';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

// Mock do hook useTemplate
vi.mock('../../hooks/useTemplate', () => ({
  useTemplate: vi.fn()
}));

const compareTemplateWithoutDynamicFields = (received: any, expected: any) => {
  const { updatedAt: _r, ...receivedWithoutDynamic } = received;
  const { updatedAt: _e, ...expectedWithoutDynamic } = expected;

  // Remove IDs dinâmicos das regras de validação
  if (receivedWithoutDynamic.validationRules) {
    receivedWithoutDynamic.validationRules = receivedWithoutDynamic.validationRules.map(
      ({ id, ...rule }: any) => rule
    );
  }
  if (expectedWithoutDynamic.validationRules) {
    expectedWithoutDynamic.validationRules = expectedWithoutDynamic.validationRules.map(
      ({ id, ...rule }: any) => rule
    );
  }

  return expect(receivedWithoutDynamic).toEqual(expectedWithoutDynamic);
};

describe('TemplateEditor', () => {
  const mockUpdateTemplate = vi.fn();
  
  const mockTemplate: Template = {
    id: '1',
    name: 'Template de Teste',
    description: 'Descrição do template de teste',
    prompt: 'Prompt inicial',
    parameters: [
      {
        name: 'param1',
        type: 'string',
        description: 'Primeiro parâmetro',
        required: true
      }
    ],
    variables: [],
    validationRules: [],
    versions: [],
    createdAt: '2024-01-01T12:00:00',
    updatedAt: '2024-01-01T12:00:00',
    createdBy: 'user1',
    isPublic: false
  };

  const mockVersions = [
    {
      id: 'v1',
      createdAt: '2024-01-01T12:00:00',
      prompt: 'Prompt inicial'
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    (useTemplate as jest.Mock).mockReturnValue({
      template: mockTemplate,
      versions: mockVersions,
      loading: false,
      error: null,
      updateTemplate: mockUpdateTemplate
    });
  });

  const renderWithRouter = (id = '1') => {
    return render(
      <MemoryRouter initialEntries={[`/templates/${id}`]}>
        <Routes>
          <Route path="/templates/:id" element={<TemplateEditor />} />
        </Routes>
      </MemoryRouter>
    );
  };

  it('deve renderizar o editor com os dados do template', () => {
    renderWithRouter();

    expect(screen.getByLabelText('Nome')).toHaveValue('Template de Teste');
    expect(screen.getByLabelText('Descrição')).toHaveValue('Descrição do template de teste');
  });

  it('deve mostrar loading state quando estiver carregando', () => {
    (useTemplate as jest.Mock).mockReturnValueOnce({
      template: null,
      versions: [],
      loading: true,
      error: null,
      updateTemplate: mockUpdateTemplate
    });

    renderWithRouter();

    expect(screen.getByText('Carregando...')).toBeInTheDocument();
  });

  it('deve atualizar o template quando os campos são alterados', async () => {
    const user = userEvent.setup();
    renderWithRouter();

    const nameInput = screen.getByLabelText('Nome') as HTMLInputElement;
    await user.clear(nameInput);
    await user.type(nameInput, 'Template de Testee');

    await waitFor(() => {
      expect(mockUpdateTemplate).toHaveBeenCalled();
      const lastCall = mockUpdateTemplate.mock.calls[mockUpdateTemplate.mock.calls.length - 1][0];
      compareTemplateWithoutDynamicFields(lastCall, {
        ...mockTemplate,
        name: 'Template de Testee'
      });
    });
  });

  it('deve alternar entre as abas corretamente', async () => {
    renderWithRouter();
    const user = userEvent.setup();

    // Clicar na aba de Variáveis
    const variablesTab = screen.getByText('Variáveis');
    await user.click(variablesTab);
    expect(screen.getByText('Adicionar Variável')).toBeInTheDocument();

    // Clicar na aba de Validação
    const validationTab = screen.getByText('Validação');
    await user.click(validationTab);
    expect(screen.getByText('Adicionar Regra')).toBeInTheDocument();
  });

  it('deve mostrar mensagem de erro quando houver erro no template', () => {
    (useTemplate as jest.Mock).mockReturnValueOnce({
      template: null,
      versions: [],
      loading: false,
      error: 'Erro ao carregar template',
      updateTemplate: mockUpdateTemplate
    });

    renderWithRouter();

    expect(screen.getByText('Erro ao carregar template')).toBeInTheDocument();
  });

  it('deve permitir adicionar um novo parâmetro', async () => {
    const user = userEvent.setup();
    renderWithRouter();

    const parametersTab = screen.getByText('Parâmetros');
    await user.click(parametersTab);

    const addButton = screen.getByText('Adicionar Parâmetro');
    await user.click(addButton);

    await waitFor(() => {
      expect(mockUpdateTemplate).toHaveBeenCalled();
      const lastCall = mockUpdateTemplate.mock.calls[mockUpdateTemplate.mock.calls.length - 1][0];
      compareTemplateWithoutDynamicFields(lastCall, {
        ...mockTemplate,
        parameters: [
          ...mockTemplate.parameters,
          {
            name: '',
            type: 'string',
            description: '',
            required: false
          }
        ]
      });
    });
  });

  it('deve permitir adicionar uma nova variável', async () => {
    const user = userEvent.setup();
    renderWithRouter();

    const variablesTab = screen.getByText('Variáveis');
    await user.click(variablesTab);

    const addButton = screen.getByText('Adicionar Variável');
    await user.click(addButton);

    await waitFor(() => {
      expect(mockUpdateTemplate).toHaveBeenCalled();
      const lastCall = mockUpdateTemplate.mock.calls[mockUpdateTemplate.mock.calls.length - 1][0];
      compareTemplateWithoutDynamicFields(lastCall, {
        ...mockTemplate,
        variables: [
          {
            name: '',
            type: 'text',
            defaultValue: '',
            required: false,
            description: ''
          }
        ]
      });
    });
  });

  it('deve permitir adicionar uma nova regra de validação', async () => {
    const user = userEvent.setup();
    renderWithRouter();

    const validationTab = screen.getByText('Validação');
    await user.click(validationTab);

    const addButton = screen.getByText('Adicionar Regra');
    await user.click(addButton);

    await waitFor(() => {
      expect(mockUpdateTemplate).toHaveBeenCalled();
      const lastCall = mockUpdateTemplate.mock.calls[mockUpdateTemplate.mock.calls.length - 1][0];
      compareTemplateWithoutDynamicFields(lastCall, {
        ...mockTemplate,
        validationRules: [
          {
            field: '',
            type: 'required',
            value: '',
            message: ''
          }
        ]
      });
    });
  });
}); 