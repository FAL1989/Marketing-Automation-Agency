import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { usePromptConfig } from '../usePromptConfig';
import { promptConfigService } from '../../services/promptConfigService';
import notificationsReducer from '../../store/slices/notificationsSlice';
import type { ReactNode } from 'react';

vi.mock('../../services/promptConfigService');

describe('usePromptConfig', () => {
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

  const wrapper = ({ children }: { children: ReactNode }) => (
    <Provider store={mockStore}>{children}</Provider>
  );

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('deve carregar configurações do prompt', async () => {
    vi.mocked(promptConfigService.getConfig).mockResolvedValueOnce(mockConfig);

    const { result } = renderHook(() => usePromptConfig(), { wrapper });

    await act(async () => {
      await result.current.loadConfig();
    });

    expect(result.current.config).toEqual(mockConfig);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('deve atualizar configurações do prompt', async () => {
    vi.mocked(promptConfigService.updateConfig).mockResolvedValueOnce();

    const { result } = renderHook(() => usePromptConfig(), { wrapper });

    await act(async () => {
      await result.current.updateConfig(mockConfig);
    });

    expect(promptConfigService.updateConfig).toHaveBeenCalledWith(mockConfig);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('deve lidar com erro ao carregar configurações', async () => {
    const error = new Error('Erro ao carregar configurações');
    vi.mocked(promptConfigService.getConfig).mockRejectedValueOnce(error);

    const { result } = renderHook(() => usePromptConfig(), { wrapper });

    await act(async () => {
      await result.current.loadConfig();
    });

    expect(result.current.config).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBe(error.message);
  });

  it('deve lidar com erro ao atualizar configurações', async () => {
    const error = new Error('Erro ao atualizar configurações');
    vi.mocked(promptConfigService.updateConfig).mockRejectedValueOnce(error);

    const { result } = renderHook(() => usePromptConfig(), { wrapper });

    await act(async () => {
      await result.current.updateConfig(mockConfig);
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBe(error.message);
  });
}); 