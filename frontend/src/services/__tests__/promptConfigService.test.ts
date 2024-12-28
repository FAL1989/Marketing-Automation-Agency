import { describe, it, expect, vi, beforeEach } from 'vitest';
import { promptConfigService } from '../promptConfigService';
import { api } from '../api';

vi.mock('../api');

describe('promptConfigService', () => {
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

  it('deve obter configurações do prompt', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockConfig });

    const config = await promptConfigService.getConfig();

    expect(api.get).toHaveBeenCalledWith('/api/prompt-config');
    expect(config).toEqual(mockConfig);
  });

  it('deve atualizar configurações do prompt', async () => {
    vi.mocked(api.put).mockResolvedValueOnce({ data: undefined });

    await promptConfigService.updateConfig(mockConfig);

    expect(api.put).toHaveBeenCalledWith('/api/prompt-config', mockConfig);
  });

  it('deve lançar erro ao falhar em obter configurações', async () => {
    const error = new Error('Erro ao obter configurações');
    vi.mocked(api.get).mockRejectedValueOnce(error);

    await expect(promptConfigService.getConfig()).rejects.toThrow(error);
  });

  it('deve lançar erro ao falhar em atualizar configurações', async () => {
    const error = new Error('Erro ao atualizar configurações');
    vi.mocked(api.put).mockRejectedValueOnce(error);

    await expect(promptConfigService.updateConfig(mockConfig)).rejects.toThrow(error);
  });
}); 