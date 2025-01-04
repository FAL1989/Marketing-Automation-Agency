import React from 'react';
import { Drawer, List, ListItem, ListItemIcon, ListItemText, Divider } from '@mui/material';
import {
    Home as HomeIcon,
    Description as TemplatesIcon,
    Create as GeneratorIcon,
    History as HistoryIcon,
    Settings as ConfigIcon,
    Analytics as AnalyticsIcon,
    SmartToy as AgentsIcon
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

const menuItems = [
    { text: 'Home', icon: <HomeIcon />, path: '/' },
    { text: 'Templates', icon: <TemplatesIcon />, path: '/templates' },
    { text: 'Generator', icon: <GeneratorIcon />, path: '/generator' },
    { text: 'History', icon: <HistoryIcon />, path: '/history' },
    { text: 'Config', icon: <ConfigIcon />, path: '/config' },
    { text: 'Analytics', icon: <AnalyticsIcon />, path: '/analytics' },
    { text: 'AI Agents', icon: <AgentsIcon />, path: '/agents' }
];

interface SidebarProps {
    open: boolean;
    onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ open, onClose }) => {
    const navigate = useNavigate();
    const location = useLocation();

    const handleNavigation = (path: string) => {
        navigate(path);
        onClose();
    };

    return (
        <Drawer
            anchor="left"
            open={open}
            onClose={onClose}
            variant="temporary"
            sx={{
                '& .MuiDrawer-paper': {
                    width: 240,
                    boxSizing: 'border-box'
                }
            }}
        >
            <List>
                {menuItems.map((item, index) => (
                    <React.Fragment key={item.text}>
                        {index === menuItems.length - 2 && <Divider />}
                        <ListItem
                            button
                            onClick={() => handleNavigation(item.path)}
                            selected={location.pathname === item.path}
                        >
                            <ListItemIcon>{item.icon}</ListItemIcon>
                            <ListItemText primary={item.text} />
                        </ListItem>
                    </React.Fragment>
                ))}
            </List>
        </Drawer>
    );
}; 