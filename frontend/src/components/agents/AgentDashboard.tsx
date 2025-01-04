import React, { useState, useMemo, useCallback } from 'react';
import { Box, Grid, Card, CardContent, Typography, CircularProgress } from '@mui/material';
import { useAgents } from '../../hooks/useAgents';
import { AgentStatus } from './AgentStatus';
import { AgentInteractions } from './AgentInteractions';
import { AgentMetrics } from './AgentMetrics';

export const AgentDashboard: React.FC = () => {
    const { agents, loading, error } = useAgents();
    const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

    // Memoize the handler to prevent unnecessary re-renders
    const handleAgentSelect = useCallback((agentId: string) => {
        setSelectedAgent(agentId);
    }, []);

    // Memoize the sections to prevent unnecessary re-renders
    const statusSection = useMemo(() => (
        <Grid item xs={12} md={4}>
            <Card>
                <CardContent>
                    <Typography variant="h6" gutterBottom>
                        Active Agents
                    </Typography>
                    <AgentStatus 
                        agents={agents}
                        onSelectAgent={handleAgentSelect}
                        selectedAgent={selectedAgent}
                    />
                </CardContent>
            </Card>
        </Grid>
    ), [agents, handleAgentSelect, selectedAgent]);

    const interactionsSection = useMemo(() => (
        <Grid item xs={12} md={8}>
            <Card>
                <CardContent>
                    <Typography variant="h6" gutterBottom>
                        Recent Interactions
                    </Typography>
                    <AgentInteractions 
                        agentId={selectedAgent}
                    />
                </CardContent>
            </Card>
        </Grid>
    ), [selectedAgent]);

    const metricsSection = useMemo(() => (
        <Grid item xs={12}>
            <Card>
                <CardContent>
                    <Typography variant="h6" gutterBottom>
                        Performance Metrics
                    </Typography>
                    <AgentMetrics 
                        agentId={selectedAgent}
                    />
                </CardContent>
            </Card>
        </Grid>
    ), [selectedAgent]);

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
                <CircularProgress />
            </Box>
        );
    }

    if (error) {
        return (
            <Box p={3}>
                <Typography color="error">
                    Error loading agents: {error}
                </Typography>
            </Box>
        );
    }

    return (
        <Box p={3}>
            <Typography variant="h4" gutterBottom>
                Agent Dashboard
            </Typography>

            <Grid container spacing={3}>
                {statusSection}
                {interactionsSection}
                {metricsSection}
            </Grid>
        </Box>
    );
}; 