import { Template, Generation } from '../types';
import { api } from '../services/api';

export const useAI = () => {
  const generateContent = async (template: Template, parameters: Record<string, any>): Promise<Generation> => {
    try {
      const { data } = await api.post<Generation>('/ai/generate', {
        templateId: template.id,
        parameters
      });
      return data;
    } catch (err) {
      console.error('Erro ao gerar conteúdo:', err);
      throw err;
    }
  };

  return {
    generateContent
  };
}; 