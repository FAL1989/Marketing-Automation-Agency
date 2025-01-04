import { useState, useEffect } from 'react';
import { AgentMetrics } from '../types/agents';
import { api } from '../services/api';

interface UseAgentMetricsReturn {
    metrics: AgentMetrics | null;
    loading: boolean;
    error: string | null;
    refetch: () => void;
}

export const useAgentMetrics = (agentId: string | null): UseAgentMetricsReturn => {
    const [metrics, setMetrics] = useState<AgentMetrics | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchMetrics = async () => {
        if (!agentId) {
            setMetrics(null);
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const response = await api.get(`/agents/${agentId}/metrics`);
            setMetrics(response.data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch metrics');
            setMetrics(null);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchMetrics();
        
        // Set up polling for real-time updates
        const interval = setInterval(fetchMetrics, 30000); // Poll every 30 seconds
        
        return () => clearInterval(interval);
    }, [agentId]);

    return {
        metrics,
        loading,
        error,
        refetch: fetchMetrics
    };
}; 