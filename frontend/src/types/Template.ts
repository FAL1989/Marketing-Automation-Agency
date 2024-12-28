export interface Parameter {
  name: string;
  label?: string;
  type: 'text' | 'number' | 'select';
  description?: string;
  required: boolean;
  placeholder?: string;
  options?: string[];
}

export interface Variable {
  name: string;
  type: string;
  description?: string;
}

export interface ValidationRule {
  field: string;
  rule: string;
  message: string;
}

export interface Version {
  id: string;
  createdAt: string;
  prompt: string;
}

export interface Template {
  id: number;
  name: string;
  description?: string;
  content: string;
  parameters: Parameter[];
  isPublic: boolean;
  isActive: boolean;
  createdAt?: string;
  updatedAt?: string;
  userId?: number;
}