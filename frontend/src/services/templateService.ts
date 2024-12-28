import { Template, CreateTemplateData } from '../types';
import { api } from './api';

export const getTemplates = async (): Promise<Template[]> => {
  const response = await api.get<Template[]>('/templates');
  return response.data;
};

export const getTemplate = async (id: number): Promise<Template> => {
  const response = await api.get<Template>(`/templates/${id}`);
  return response.data;
};

export const createTemplate = async (template: CreateTemplateData): Promise<Template> => {
  const formattedTemplate = {
    ...template,
    parameters: template.parameters.map(param => ({
      name: param.name,
      label: param.label || param.name,
      type: param.type,
      description: param.description || '',
      required: param.required,
      placeholder: param.placeholder || '',
      options: param.type === 'select' ? param.options || [] : undefined
    }))
  };

  const response = await api.post<Template>('/templates', formattedTemplate);
  return response.data;
};

export const updateTemplate = async (id: number, template: Partial<Template>): Promise<Template> => {
  const formattedTemplate = {
    ...template,
    parameters: template.parameters?.map(param => ({
      name: param.name,
      label: param.label || param.name,
      type: param.type,
      description: param.description || '',
      required: param.required,
      placeholder: param.placeholder || '',
      options: param.type === 'select' ? param.options || [] : undefined
    }))
  };

  const response = await api.put<Template>(`/templates/${id}`, formattedTemplate);
  return response.data;
};

export const deleteTemplate = async (id: number): Promise<void> => {
  await api.delete(`/templates/${id}`);
}; 