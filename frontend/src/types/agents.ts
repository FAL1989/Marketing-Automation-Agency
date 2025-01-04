export interface Agent {
    id: string;
    name: string;
    description: string;
    status: 'active' | 'error' | 'idle';
    type: 'requirements' | 'code' | 'architecture' | 'security';
    capabilities: string[];
    lastActive?: string;
    metrics?: AgentMetrics;
}

export interface AgentMetrics {
    successRate: number;
    averageResponseTime: number;
    totalRequests: number;
    errorRate: number;
    lastError?: string;
}

export interface AgentInteraction {
    id: string;
    agentId: string;
    timestamp: string;
    type: 'request' | 'response' | 'error';
    content: string;
    metadata?: Record<string, any>;
}

export interface AgentAnalysis {
    requirements?: string;
    architecture?: string;
    security?: string;
    code?: string;
}

export interface AgentRequest {
    content: string;
    mode?: string;
    context?: string;
    originalCode?: string;
}

export interface AgentResponse {
    result: string;
    analysis?: AgentAnalysis;
    metadata?: Record<string, any>;
} 