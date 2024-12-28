import { api } from './api';

interface AnalyticsData {
  totalTemplates: number;
  totalContents: number;
  averageGenerationTime: number;
  successRate: number;
  popularTemplates: Array<{
    id: string;
    name: string;
    usageCount: number;
  }>;
}

export const analyticsService = {
  getAnalytics: async (): Promise<AnalyticsData> => {
    const response = await api.get('/analytics');
    return response.data;
  },
  
  getTemplateUsage: async (templateId: string) => {
    const response = await api.get(`/analytics/templates/${templateId}`);
    return response.data;
  },
  
  getGenerationStats: async (period: 'day' | 'week' | 'month') => {
    const response = await api.get(`/analytics/generations?period=${period}`);
    return response.data;
  }
}; 