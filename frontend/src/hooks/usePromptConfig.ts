import { useState, useCallback } from 'react';
import { PromptConfig } from '../types';
import { promptConfigService } from '../services/promptConfigService';
import { useNotifications } from './useNotifications';

export const usePromptConfig = () => {
  const [config, setConfig] = useState<PromptConfig | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { showNotification } = useNotifications();

  const loadConfig = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await promptConfigService.getConfig();
      setConfig(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro ao carregar configurações';
      setError(message);
      showNotification({ type: 'error', message });
    } finally {
      setIsLoading(false);
    }
  }, [showNotification]);

  const updateConfig = useCallback(async (newConfig: PromptConfig) => {
    try {
      setIsLoading(true);
      setError(null);
      await promptConfigService.updateConfig(newConfig);
      setConfig(newConfig);
      showNotification({ type: 'success', message: 'Configurações atualizadas com sucesso!' });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro ao atualizar configurações';
      setError(message);
      showNotification({ type: 'error', message });
    } finally {
      setIsLoading(false);
    }
  }, [showNotification]);

  return {
    config,
    isLoading,
    error,
    loadConfig,
    updateConfig
  };
}; 