export interface Template {
  id: string;
  name: string;
  description: string;
  parameters: TemplateParameter[];
  createdAt: string;
  updatedAt: string;
}

export interface TemplateParameter {
  name: string;
  type: 'text' | 'number' | 'select';
  description: string;
  required: boolean;
  options?: string[]; // Para parâmetros do tipo 'select'
}

export interface GeneratedContent {
  id: string;
  templateId: string;
  content: string;
  parameters: Record<string, any>;
  createdAt: string;
  status: 'pending' | 'completed' | 'failed';
  error?: string;
}

export interface ContentGenerationRequest {
  templateId: string;
  parameters: Record<string, any>;
} 