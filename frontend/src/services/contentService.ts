import { get, post, put, del } from './api';
import { Template, Generation, PaginatedResponse, CreateTemplateData, ApiResponse } from '../types';

export const contentService = {
    // Templates
    getTemplates: async (): Promise<Template[]> => {
        const response = await get<ApiResponse<Template[]>>('/templates');
        return response.data;
    },
    
    getTemplate: (id: number): Promise<Template> => 
        get<ApiResponse<Template>>(`/templates/${id}`).then(res => res.data),
    
    createTemplate: (template: CreateTemplateData): Promise<Template> =>
        post<ApiResponse<Template>>('/templates', template).then(res => res.data),
    
    updateTemplate: (id: number, template: Partial<Template>): Promise<Template> =>
        put<ApiResponse<Template>>(`/templates/${id}`, template).then(res => res.data),
    
    deleteTemplate: async (id: number): Promise<void> => {
        await del<void>(`/templates/${id}`);
    },
    
    // Generations
    generateContent: (templateId: number, parameters: Record<string, any>): Promise<Generation> =>
        post<ApiResponse<Generation>>('/contents/generate', { templateId, parameters }).then(res => res.data),
    
    getGenerations: (page = 1, pageSize = 10) =>
        get<PaginatedResponse<Generation>>(`/generations?page=${page}&pageSize=${pageSize}`),
    
    getGeneration: (id: string): Promise<Generation> => 
        get<ApiResponse<Generation>>(`/generations/${id}`).then(res => res.data),
    
    // Analytics
    getAnalytics: () =>
        get<ApiResponse<{
            todayGenerations: number;
            successRate: number;
            avgGenerationTime: number;
            generationTrend: number;
            successTrend: number;
            timeTrend: number;
        }>>('/analytics').then(res => res.data),
    
    // Template Usage
    getTemplateUsage: (templateId: number) =>
        get<ApiResponse<{
            totalUses: number;
            successRate: number;
            avgGenerationTime: number;
            lastUsed: string;
        }>>(`/templates/${templateId}/usage`).then(res => res.data)
}; 