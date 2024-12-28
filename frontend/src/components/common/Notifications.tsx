import React from 'react';
import { Box, Alert, AlertIcon, AlertTitle, AlertDescription, Stack } from '@chakra-ui/react';

interface Notification {
  id?: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  duration?: number;
}

interface NotificationsContextData {
  notifications: Notification[];
  addNotification: (notification: Notification) => void;
  removeNotification: (id: string) => void;
}

export const NotificationsContext = React.createContext<NotificationsContextData>({} as NotificationsContextData);

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = React.useState<Notification[]>([]);

  const addNotification = (notification: Notification) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newNotification = { ...notification, id };
    setNotifications((prev) => [...prev, newNotification]);

    if (notification.duration) {
      setTimeout(() => {
        removeNotification(id);
      }, notification.duration);
    }
  };

  const removeNotification = (id: string) => {
    setNotifications((prev) => prev.filter((notification) => notification.id !== id));
  };

  return (
    <NotificationsContext.Provider value={{ notifications, addNotification, removeNotification }}>
      {children}
      <Box position="fixed" top={4} right={4} zIndex={9999}>
        <Stack spacing={2}>
          {notifications.map((notification) => (
            <Alert
              key={notification.id}
              status={notification.type}
              variant="solid"
              borderRadius="md"
            >
              <AlertIcon />
              <Box>
                <AlertTitle>{notification.title}</AlertTitle>
                <AlertDescription>{notification.message}</AlertDescription>
              </Box>
            </Alert>
          ))}
        </Stack>
      </Box>
    </NotificationsContext.Provider>
  );
};

export const useNotifications = () => {
  const context = React.useContext(NotificationsContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};

export const Notifications = NotificationProvider; 