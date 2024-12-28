import { Generation } from '../types';
import { api } from './api';

export const getGenerations = async (): Promise<Generation[]> => {
  const response = await api.get<Generation[]>('/generations');
  return response.data;
};

export const getGeneration = async (id: string): Promise<Generation> => {
  const response = await api.get<Generation>(`/generations/${id}`);
  return response.data;
};

export const createGeneration = async (
  templateId: string,
  parameters: Record<string, string | number>
): Promise<Generation> => {
  const response = await api.post<Generation>('/generations', {
    templateId,
    parameters,
  });
  return response.data;
};

export const cancelGeneration = async (id: string): Promise<void> => {
  await api.post(`/generations/${id}/cancel`);
};

export const retryGeneration = async (id: string): Promise<Generation> => {
  const response = await api.post<Generation>(`/generations/${id}/retry`);
  return response.data;
}; 