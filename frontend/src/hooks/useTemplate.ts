import { useState, useEffect } from 'react';
import { Template } from '../types';
import { api } from '../services/api';

interface UseTemplateReturn {
  template: Template | null;
  loading: boolean;
  error: string | null;
  updateTemplate: (template: Partial<Template>) => Promise<void>;
}

export function useTemplate(id?: string): UseTemplateReturn {
  const [template, setTemplate] = useState<Template | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) {
      setLoading(false);
      return;
    }

    const fetchTemplate = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await api.get(`/templates/${id}`);
        setTemplate(response.data);
      } catch (err) {
        console.error('Erro ao carregar template:', err);
        setError('Não foi possível carregar o template. Por favor, tente novamente.');
      } finally {
        setLoading(false);
      }
    };

    fetchTemplate();
  }, [id]);

  const updateTemplate = async (updatedTemplate: Partial<Template>) => {
    if (!id) return;

    try {
      setLoading(true);
      setError(null);
      const now = new Date().toISOString();
      const response = await api.put(`/templates/${id}`, {
        ...template,
        ...updatedTemplate,
        updatedAt: now,
        versions: template?.versions || []
      });

      setTemplate(response.data);
    } catch (err) {
      console.error('Erro ao atualizar template:', err);
      throw new Error('Não foi possível atualizar o template. Por favor, tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  return {
    template,
    loading,
    error,
    updateTemplate
  };
} 