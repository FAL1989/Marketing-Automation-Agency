import { FC } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Box, List, ListItem, ListItemIcon, ListItemText } from '@mui/material';
import HomeIcon from '@mui/icons-material/Home';
import TemplateIcon from '@mui/icons-material/Description';
import SettingsIcon from '@mui/icons-material/Settings';
import AnalyticsIcon from '@mui/icons-material/Analytics';

export const Navigation: FC = () => {
  const location = useLocation();

  const menuItems = [
    { path: '/', label: 'Início', icon: <HomeIcon /> },
    { path: '/templates', label: 'Templates', icon: <TemplateIcon /> },
    { path: '/config', label: 'Configurações', icon: <SettingsIcon /> },
    { path: '/analytics', label: 'Métricas', icon: <AnalyticsIcon /> }
  ];

  return (
    <Box component="nav">
      <List>
        {menuItems.map(item => (
          <ListItem
            key={item.path}
            component={Link}
            to={item.path}
            selected={location.pathname === item.path}
            sx={{
              color: 'text.primary',
              '&.Mui-selected': {
                backgroundColor: 'action.selected',
                '&:hover': {
                  backgroundColor: 'action.hover'
                }
              }
            }}
          >
            <ListItemIcon sx={{ color: 'inherit' }}>{item.icon}</ListItemIcon>
            <ListItemText primary={item.label} />
          </ListItem>
        ))}
      </List>
    </Box>
  );
}; 