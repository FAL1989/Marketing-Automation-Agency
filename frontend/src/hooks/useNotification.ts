import { useCallback } from 'react';
import { toast } from 'react-toastify';

export type NotificationType = 'success' | 'error' | 'info' | 'warning';

export const useNotification = () => {
  const showNotification = useCallback((message: string, type: NotificationType = 'info') => {
    toast[type](message, {
      position: 'top-right',
      autoClose: 5000,
      hideProgressBar: false,
      closeOnClick: true,
      pauseOnHover: true,
      draggable: true,
    });
  }, []);

  return {
    showNotification,
    showSuccess: (message: string) => showNotification(message, 'success'),
    showError: (message: string) => showNotification(message, 'error'),
    showWarning: (message: string) => showNotification(message, 'warning'),
    showInfo: (message: string) => showNotification(message, 'info'),
  };
}; 