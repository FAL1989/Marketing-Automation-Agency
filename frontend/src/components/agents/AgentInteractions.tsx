import React from 'react';
import {
    Timeline,
    TimelineItem,
    TimelineSeparator,
    TimelineConnector,
    TimelineContent,
    TimelineDot
} from '@mui/lab';
import {
    Paper,
    Typography,
    Box,
    Chip,
    IconButton,
    Tooltip
} from '@mui/material';
import {
    Send as RequestIcon,
    Reply as ResponseIcon,
    Error as ErrorIcon,
    ContentCopy as CopyIcon
} from '@mui/icons-material';
import { useAgentInteractions } from '../../hooks/useAgentInteractions';
import { AgentInteraction } from '../../types/agents';
import { formatDistanceToNow } from 'date-fns';

interface AgentInteractionsProps {
    agentId: string | null;
}

export const AgentInteractions: React.FC<AgentInteractionsProps> = ({ agentId }) => {
    const { interactions, loading, error } = useAgentInteractions(agentId);

    const getInteractionIcon = (type: string) => {
        switch (type) {
            case 'request':
                return <RequestIcon />;
            case 'response':
                return <ResponseIcon />;
            case 'error':
                return <ErrorIcon color="error" />;
            default:
                return null;
        }
    };

    const getInteractionColor = (type: string) => {
        switch (type) {
            case 'request':
                return 'primary';
            case 'response':
                return 'success';
            case 'error':
                return 'error';
            default:
                return 'grey';
        }
    };

    const copyToClipboard = (content: string) => {
        navigator.clipboard.writeText(content);
    };

    if (!agentId) {
        return (
            <Box p={2}>
                <Typography color="textSecondary">
                    Select an agent to view interactions
                </Typography>
            </Box>
        );
    }

    if (loading) {
        return (
            <Box p={2}>
                <Typography>Loading interactions...</Typography>
            </Box>
        );
    }

    if (error) {
        return (
            <Box p={2}>
                <Typography color="error">
                    Error loading interactions: {error}
                </Typography>
            </Box>
        );
    }

    return (
        <Timeline>
            {interactions.map((interaction: AgentInteraction) => (
                <TimelineItem key={interaction.id}>
                    <TimelineSeparator>
                        <TimelineDot color={getInteractionColor(interaction.type) as any}>
                            {getInteractionIcon(interaction.type)}
                        </TimelineDot>
                        <TimelineConnector />
                    </TimelineSeparator>
                    <TimelineContent>
                        <Paper elevation={1} sx={{ p: 2, mb: 2 }}>
                            <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                                <Chip
                                    label={interaction.type}
                                    size="small"
                                    color={getInteractionColor(interaction.type) as any}
                                />
                                <Typography variant="caption" color="textSecondary">
                                    {formatDistanceToNow(new Date(interaction.timestamp), { addSuffix: true })}
                                </Typography>
                            </Box>
                            <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                                <Typography
                                    variant="body2"
                                    sx={{
                                        whiteSpace: 'pre-wrap',
                                        maxHeight: '100px',
                                        overflow: 'auto'
                                    }}
                                >
                                    {interaction.content}
                                </Typography>
                                <Tooltip title="Copy content">
                                    <IconButton
                                        size="small"
                                        onClick={() => copyToClipboard(interaction.content)}
                                    >
                                        <CopyIcon fontSize="small" />
                                    </IconButton>
                                </Tooltip>
                            </Box>
                            {interaction.metadata && (
                                <Box mt={1}>
                                    <Typography variant="caption" color="textSecondary">
                                        Metadata: {JSON.stringify(interaction.metadata)}
                                    </Typography>
                                </Box>
                            )}
                        </Paper>
                    </TimelineContent>
                </TimelineItem>
            ))}
        </Timeline>
    );
}; 