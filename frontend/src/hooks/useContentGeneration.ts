import { useState, useCallback } from 'react';
import { contentService } from '../services/contentService';
import { ContentGenerationRequest, GeneratedContent } from '../types/content';

export const useContentGeneration = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generatedContent, setGeneratedContent] = useState<GeneratedContent | null>(null);

  const generateContent = useCallback(async (request: ContentGenerationRequest) => {
    setIsLoading(true);
    setError(null);
    try {
      const content = await contentService.generateContent(request);
      setGeneratedContent(content);
      return content;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro ao gerar conteúdo';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const checkGenerationStatus = useCallback(async (contentId: string) => {
    try {
      const content = await contentService.getGeneratedContent(contentId);
      setGeneratedContent(content);
      return content;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro ao verificar status da geração';
      setError(errorMessage);
      throw err;
    }
  }, []);

  return {
    isLoading,
    error,
    generatedContent,
    generateContent,
    checkGenerationStatus
  };
}; 