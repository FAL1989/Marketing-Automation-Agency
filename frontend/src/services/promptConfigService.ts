import { PromptConfig } from '../types';
import { api } from './api';

export const promptConfigService = {
  async getConfig(): Promise<PromptConfig> {
    const response = await api.get<PromptConfig>('/api/prompt-config');
    return response.data;
  },

  async updateConfig(config: PromptConfig): Promise<void> {
    await api.put('/api/prompt-config', config);
  }
}; 