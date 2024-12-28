import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { PromptConfig } from '../../components/PromptConfig';
import { usePromptConfig } from '../../hooks/usePromptConfig';
import notificationsReducer from '../../store/slices/notificationsSlice';

vi.mock('../../hooks/usePromptConfig');

describe('PromptConfig', () => {
  const mockStore = configureStore({
    reducer: {
      notifications: notificationsReducer
    }
  });

  const mockConfig = {
    provider: 'openai',
    model: 'gpt-3.5-turbo',
    temperature: 0.7,
    maxTokens: 2048,
    topP: 1,
    frequencyPenalty: 0,
    presencePenalty: 0
  };

  const mockOnSave = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(usePromptConfig).mockReturnValue({
      config: mockConfig,
      isLoading: false,
      error: null,
      loadConfig: vi.fn(),
      updateConfig: vi.fn()
    });
  });

  it('deve renderizar o formulário com valores iniciais', () => {
    render(
      <Provider store={mockStore}>
        <PromptConfig onSave={mockOnSave} />
      </Provider>
    );

    expect(screen.getByText('OpenAI')).toBeInTheDocument();
    expect(screen.getByText('GPT-3.5 Turbo')).toBeInTheDocument();
    expect(screen.getByText('Temperatura')).toBeInTheDocument();
    expect(screen.getByText('Máximo de Tokens')).toBeInTheDocument();
  });

  it('deve exibir loading state', () => {
    vi.mocked(usePromptConfig).mockReturnValue({
      config: null,
      isLoading: true,
      error: null,
      loadConfig: vi.fn(),
      updateConfig: vi.fn()
    });

    render(
      <Provider store={mockStore}>
        <PromptConfig onSave={mockOnSave} />
      </Provider>
    );

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('deve exibir mensagem de erro', () => {
    const error = 'Erro ao carregar configurações';
    vi.mocked(usePromptConfig).mockReturnValue({
      config: null,
      isLoading: false,
      error,
      loadConfig: vi.fn(),
      updateConfig: vi.fn()
    });

    render(
      <Provider store={mockStore}>
        <PromptConfig onSave={mockOnSave} />
      </Provider>
    );

    expect(screen.getByText(error)).toBeInTheDocument();
  });

  it('deve chamar onSave ao submeter o formulário', async () => {
    const mockUpdateConfig = vi.fn();
    vi.mocked(usePromptConfig).mockReturnValue({
      config: mockConfig,
      isLoading: false,
      error: null,
      loadConfig: vi.fn(),
      updateConfig: mockUpdateConfig
    });

    render(
      <Provider store={mockStore}>
        <PromptConfig onSave={mockOnSave} />
      </Provider>
    );

    const saveButton = screen.getByText('Salvar');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockUpdateConfig).toHaveBeenCalledWith(mockConfig);
      expect(mockOnSave).toHaveBeenCalledWith(mockConfig);
    });
  });
}); 