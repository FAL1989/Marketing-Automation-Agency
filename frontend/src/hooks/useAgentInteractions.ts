import { useState, useEffect } from 'react';
import { AgentInteraction } from '../types/agents';
import { api } from '../services/api';

interface UseAgentInteractionsReturn {
    interactions: AgentInteraction[];
    loading: boolean;
    error: string | null;
    refetch: () => void;
}

export const useAgentInteractions = (agentId: string | null): UseAgentInteractionsReturn => {
    const [interactions, setInteractions] = useState<AgentInteraction[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchInteractions = async () => {
        if (!agentId) {
            setInteractions([]);
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const response = await api.get(`/agents/${agentId}/interactions`);
            setInteractions(response.data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch interactions');
            setInteractions([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchInteractions();
    }, [agentId]);

    return {
        interactions,
        loading,
        error,
        refetch: fetchInteractions
    };
}; 