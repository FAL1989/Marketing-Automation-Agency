import { useState, useEffect } from 'react';
import { Agent } from '../types/agents';
import { api } from '../services/api';

interface UseAgentsReturn {
    agents: Agent[];
    loading: boolean;
    error: string | null;
    refetch: () => void;
}

export const useAgents = (): UseAgentsReturn => {
    const [agents, setAgents] = useState<Agent[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchAgents = async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await api.get('/agents');
            setAgents(response.data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch agents');
            setAgents([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchAgents();
    }, []);

    return {
        agents,
        loading,
        error,
        refetch: fetchAgents
    };
}; 