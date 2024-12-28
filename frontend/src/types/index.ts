// Template types
export interface Parameter {
    name: string;
    type: 'string' | 'number' | 'boolean' | 'array' | 'object';
    description?: string;
    required: boolean;
    defaultValue?: any;
    validation?: ValidationRule[];
}

export interface Template {
    id: number;
    name: string;
    description: string;
    content: string;
    parameters: TemplateParameter[];
    createdAt: string;
    updatedAt: string;
    userId?: number;
    isPublic: boolean;
    isActive: boolean;
    tags?: string[];
}

export interface TemplateParameter {
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
    type: 'string' | 'number' | 'boolean' | 'array' | 'object';
    description?: string;
    defaultValue?: any;
}

export interface ValidationRule {
    type: 'required' | 'min' | 'max' | 'pattern' | 'custom';
    value?: any;
    message: string;
    validator?: (value: any) => boolean;
}

export interface Version {
    id: number;
    prompt: string;
    parameters: Parameter[];
    createdAt: string;
    createdBy: string;
    isActive: boolean;
}

export interface TemplateUsage {
    totalGenerations: number;
    successRate: number;
    averageTime: number;
    lastUsed: string;
}

export interface AIConfig {
    provider: 'openai' | 'anthropic' | 'cohere';
    model: string;
    temperature: number;
    maxTokens: number;
    stopSequences?: string[];
    frequencyPenalty?: number;
    presencePenalty?: number;
    topP?: number;
}

// Generation types
export interface Generation {
    id: number;
    templateId: number;
    userId: number;
    status: 'pending' | 'success' | 'error';
    result: string | null;
    content: string;
    error: string | null;
    createdAt: string;
    completedAt: string | null;
    metadata: Record<string, any>;
}

// Analytics types
export interface AnalyticsData {
    todayGenerations: number;
    successRate: number;
    averageResponseTime: number;
    costPerGeneration: number;
    generationTrend: number;
    successTrend: number;
    timeTrend: number;
    errorDistribution: Record<string, number>;
    templateMetrics: TemplateMetric[];
}

export interface PromptConfig {
    provider: string;
    model: string;
    temperature: number;
    maxTokens: number;
    topP: number;
    frequencyPenalty: number;
    presencePenalty: number;
}

// User types
export interface User {
    id: string;
    email: string;
    name: string;
    role: 'user' | 'admin';
    createdAt: string;
    updatedAt: string;
}

// API Response types
export interface ApiResponse<T> {
    data: T;
    message?: string;
    error?: string;
}

export interface PaginatedResponse<T> {
    data: T[];
    total: number;
    page: number;
    pageSize: number;
    totalPages: number;
}

export interface UserSettings {
  theme: 'light' | 'dark' | 'system';
  language: string;
  notifications: {
    email: boolean;
    push: boolean;
    frequency: 'realtime' | 'daily' | 'weekly';
  };
  defaultTemplate: string | null;
  aiProvider: string;
  security: {
    mfaEnabled: boolean;
    sessionTimeout: number;
  };
}

export interface AuthContextData {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => void;
}

export interface Metrics {
  totalGenerations: number;
  successRate: number;
  averageTime: number;
  activeTemplates: number;
  recentGenerations: Generation[];
  popularTemplates: Array<{
    templateId: string;
    name: string;
    usageCount: number;
  }>;
}

export type NotificationType = 'success' | 'error' | 'info' | 'warning'; 

export interface DailyGeneration {
  date: string;
  count: number;
}

export interface TemplateMetric {
  templateId: number;
  templateName: string;
  totalGenerations: number;
  successRate: number;
  averageTime: number;
}

export interface TemplateTime {
  templateId: string;
  name: string;
  avgTime: number;
}

export interface ErrorDistribution {
  type: string;
  count: number;
}

export interface MetricCardProps {
  title: string;
  value: string | number;
  icon: MetricIcon;
  trend?: {
    value: number;
    label: string;
  };
}

export type MetricIcon = React.ForwardRefExoticComponent<
  Omit<React.SVGProps<SVGSVGElement>, 'ref'> & {
    title?: string;
    titleId?: string;
  } & React.RefAttributes<SVGSVGElement>
>;

export interface AuthResponse {
  token: string;
  user: User;
}

export interface ErrorResponse {
  message: string;
  code?: string;
  details?: Record<string, any>;
}

export interface CreateTemplateData {
    name: string;
    description?: string;
    content: string;
    parameters: TemplateParameter[];
    isPublic: boolean;
}