import { vi } from 'vitest';
import { Template } from '../types';

const mockTemplate: Template = {
  id: '1',
  name: 'Template de Teste',
  description: 'Descrição do template de teste',
  prompt: 'Prompt de teste',
  variables: [],
  validationRules: [],
  createdAt: new Date('2024-01-01T12:00:00'),
  updatedAt: new Date('2024-01-01T12:00:00'),
  createdBy: 'user1',
  isPublic: false
};

const mockVersions = [
  {
    id: 'v1',
    version: 1,
    createdAt: new Date('2024-01-01T12:00:00'),
    createdBy: 'user1',
    changes: ['Criação inicial'],
    snapshot: { ...mockTemplate }
  }
];

export const useTemplate = vi.fn().mockReturnValue({
  template: mockTemplate,
  versions: mockVersions,
  loading: false,
  error: null,
  updateTemplate: vi.fn()
}); 