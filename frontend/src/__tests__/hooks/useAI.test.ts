import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useAI } from '../../hooks/useAI';
import { Generation } from '../../types';
import { api } from '../../services/api';

vi.mock('../../services/api', () => ({
  api: {
    post: vi.fn()
  }
}));

describe('useAI', () => {
  const mockTemplate = {
    id: '1',
    name: 'Test Template',
    description: 'Test Description',
    prompt: 'Test Prompt',
    variables: [],
    validationRules: [],
    parameters: [],
    versions: [],
    createdAt: '2024-01-01T00:00:00.000Z',
    updatedAt: '2024-01-01T00:00:00.000Z',
    createdBy: 'test-user',
    isPublic: false
  };

  const mockParameters = {
    param1: 'value1',
    param2: 'value2'
  };

  const mockGeneration: Generation = {
    id: '1',
    templateId: '1',
    content: 'Generated content',
    status: 'success',
    parameters: mockParameters,
    createdAt: '2024-01-01T00:00:00.000Z',
    updatedAt: '2024-01-01T00:00:00.000Z',
    error: undefined
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('deve chamar a API com os parâmetros corretos', async () => {
    const mockPost = vi.fn().mockResolvedValueOnce({ data: mockGeneration });
    vi.mocked(api.post).mockImplementation(mockPost);

    const { result } = renderHook(() => useAI());
    const response = await result.current.generateContent(mockTemplate, mockParameters);

    expect(mockPost).toHaveBeenCalledWith('/ai/generate', {
      templateId: mockTemplate.id,
      parameters: mockParameters
    });
    expect(response).toEqual(mockGeneration);
  });

  it('deve lançar erro quando a API falha', async () => {
    const error = new Error('API Error');
    vi.mocked(api.post).mockRejectedValueOnce(error);

    const { result } = renderHook(() => useAI());
    
    await expect(
      result.current.generateContent(mockTemplate, mockParameters)
    ).rejects.toThrow('API Error');
  });
}); 