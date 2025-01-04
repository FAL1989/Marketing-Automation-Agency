import React from 'react';
import { Container, Typography } from '@mui/material';
import { AgentDashboard } from '../components/agents/AgentDashboard';

export const AgentDashboardPage: React.FC = () => {
    return (
        <Container maxWidth="xl">
            <Typography variant="h4" gutterBottom sx={{ mb: 4 }}>
                AI Agents
            </Typography>
            <AgentDashboard />
        </Container>
    );
}; 