import React from 'react';
import { 
    List, 
    ListItem, 
    ListItemText, 
    ListItemIcon,
    ListItemButton,
    Chip,
    Box,
    Tooltip
} from '@mui/material';
import {
    CheckCircle as ActiveIcon,
    Error as ErrorIcon,
    HourglassEmpty as IdleIcon
} from '@mui/icons-material';
import { Agent } from '../../types/agents';

interface AgentStatusProps {
    agents: Agent[];
    selectedAgent: string | null;
    onSelectAgent: (agentId: string) => void;
}

export const AgentStatus: React.FC<AgentStatusProps> = ({
    agents,
    selectedAgent,
    onSelectAgent
}) => {
    const getStatusIcon = (status: string) => {
        switch (status.toLowerCase()) {
            case 'active':
                return <ActiveIcon color="success" />;
            case 'error':
                return <ErrorIcon color="error" />;
            default:
                return <IdleIcon color="disabled" />;
        }
    };

    const getStatusColor = (status: string) => {
        switch (status.toLowerCase()) {
            case 'active':
                return 'success';
            case 'error':
                return 'error';
            default:
                return 'default';
        }
    };

    return (
        <List>
            {agents.map((agent) => (
                <ListItem
                    key={agent.id}
                    disablePadding
                    secondaryAction={
                        <Chip
                            label={agent.status}
                            color={getStatusColor(agent.status) as any}
                            size="small"
                        />
                    }
                >
                    <ListItemButton
                        selected={selectedAgent === agent.id}
                        onClick={() => onSelectAgent(agent.id)}
                    >
                        <ListItemIcon>
                            {getStatusIcon(agent.status)}
                        </ListItemIcon>
                        <ListItemText
                            primary={agent.name}
                            secondary={
                                <Tooltip title={agent.description}>
                                    <Box
                                        component="span"
                                        sx={{
                                            display: '-webkit-box',
                                            WebkitLineClamp: 2,
                                            WebkitBoxOrient: 'vertical',
                                            overflow: 'hidden',
                                            textOverflow: 'ellipsis'
                                        }}
                                    >
                                        {agent.description}
                                    </Box>
                                </Tooltip>
                            }
                        />
                    </ListItemButton>
                </ListItem>
            ))}
        </List>
    );
}; 