import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { PromptConfigPage } from '../../pages/PromptConfigPage';
import { promptConfigService } from '../../services/promptConfigService';
import notificationsReducer from '../../store/slices/notificationsSlice';

vi.mock('../../services/promptConfigService');

describe('PromptConfigPage', () => {
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

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('deve renderizar o título da página', () => {
    vi.mocked(promptConfigService.getConfig).mockResolvedValueOnce(mockConfig);

    render(
      <Provider store={mockStore}>
        <PromptConfigPage />
      </Provider>
    );

    expect(screen.getByText('Configuração de Prompts')).toBeInTheDocument();
  });

  it('deve carregar e exibir as configurações', async () => {
    vi.mocked(promptConfigService.getConfig).mockResolvedValueOnce(mockConfig);

    render(
      <Provider store={mockStore}>
        <PromptConfigPage />
      </Provider>
    );

    await waitFor(() => {
      expect(screen.getByText('OpenAI')).toBeInTheDocument();
      expect(screen.getByText('GPT-3.5 Turbo')).toBeInTheDocument();
    });
  });

  it('deve exibir mensagem de erro ao falhar em carregar configurações', async () => {
    const error = new Error('Erro ao carregar configurações');
    vi.mocked(promptConfigService.getConfig).mockRejectedValueOnce(error);

    render(
      <Provider store={mockStore}>
        <PromptConfigPage />
      </Provider>
    );

    await waitFor(() => {
      expect(screen.getByText(error.message)).toBeInTheDocument();
    });
  });
}); 