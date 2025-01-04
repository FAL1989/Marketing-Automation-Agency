import React from 'react';
import {
    Grid,
    Paper,
    Typography,
    Box,
    LinearProgress,
    Tooltip
} from '@mui/material';
import {
    CheckCircle as SuccessIcon,
    Timer as TimeIcon,
    Error as ErrorIcon,
    Assessment as RequestsIcon
} from '@mui/icons-material';
import { useAgentMetrics } from '../../hooks/useAgentMetrics';

interface AgentMetricsProps {
    agentId: string | null;
}

interface MetricCardProps {
    title: string;
    value: number;
    icon: React.ReactNode;
    color: string;
    unit?: string;
    tooltip?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({
    title,
    value,
    icon,
    color,
    unit,
    tooltip
}) => (
    <Tooltip title={tooltip || ''}>
        <Paper
            elevation={1}
            sx={{
                p: 2,
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between'
            }}
        >
            <Box display="flex" justifyContent="space-between" alignItems="center">
                <Typography variant="subtitle2" color="textSecondary">
                    {title}
                </Typography>
                <Box sx={{ color }}>{icon}</Box>
            </Box>
            <Box mt={2}>
                <Typography variant="h4" component="div">
                    {value}
                    {unit && (
                        <Typography variant="caption" component="span" ml={0.5}>
                            {unit}
                        </Typography>
                    )}
                </Typography>
                <LinearProgress
                    variant="determinate"
                    value={Math.min(value, 100)}
                    sx={{
                        mt: 1,
                        backgroundColor: `${color}22`,
                        '& .MuiLinearProgress-bar': {
                            backgroundColor: color
                        }
                    }}
                />
            </Box>
        </Paper>
    </Tooltip>
);

export const AgentMetrics: React.FC<AgentMetricsProps> = ({ agentId }) => {
    const { metrics, loading, error } = useAgentMetrics(agentId);

    if (!agentId) {
        return (
            <Box p={2}>
                <Typography color="textSecondary">
                    Select an agent to view metrics
                </Typography>
            </Box>
        );
    }

    if (loading) {
        return (
            <Box p={2}>
                <Typography>Loading metrics...</Typography>
            </Box>
        );
    }

    if (error) {
        return (
            <Box p={2}>
                <Typography color="error">
                    Error loading metrics: {error}
                </Typography>
            </Box>
        );
    }

    if (!metrics) {
        return (
            <Box p={2}>
                <Typography color="textSecondary">
                    No metrics available
                </Typography>
            </Box>
        );
    }

    return (
        <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
                <MetricCard
                    title="Success Rate"
                    value={metrics.successRate}
                    icon={<SuccessIcon />}
                    color="#4caf50"
                    unit="%"
                    tooltip="Percentage of successful requests"
                />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
                <MetricCard
                    title="Response Time"
                    value={metrics.averageResponseTime}
                    icon={<TimeIcon />}
                    color="#2196f3"
                    unit="ms"
                    tooltip="Average response time in milliseconds"
                />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
                <MetricCard
                    title="Error Rate"
                    value={metrics.errorRate}
                    icon={<ErrorIcon />}
                    color="#f44336"
                    unit="%"
                    tooltip="Percentage of failed requests"
                />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
                <MetricCard
                    title="Total Requests"
                    value={metrics.totalRequests}
                    icon={<RequestsIcon />}
                    color="#ff9800"
                    tooltip="Total number of requests processed"
                />
            </Grid>
            {metrics.lastError && (
                <Grid item xs={12}>
                    <Paper elevation={1} sx={{ p: 2 }}>
                        <Typography variant="subtitle2" color="error" gutterBottom>
                            Last Error
                        </Typography>
                        <Typography variant="body2">
                            {metrics.lastError}
                        </Typography>
                    </Paper>
                </Grid>
            )}
        </Grid>
    );
}; 