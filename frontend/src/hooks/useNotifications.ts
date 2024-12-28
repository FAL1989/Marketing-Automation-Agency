import { useCallback } from 'react';
import { useDispatch } from 'react-redux';
import { addNotification } from '../store/slices/notificationsSlice';
import { NotificationType } from '../types';

interface ShowNotificationParams {
  type: NotificationType;
  message: string;
  duration?: number;
}

export const useNotifications = () => {
  const dispatch = useDispatch();

  const showNotification = useCallback(
    ({ type, message, duration = 5000 }: ShowNotificationParams) => {
      dispatch(
        addNotification({
          id: Date.now().toString(),
          type,
          message,
          duration
        })
      );
    },
    [dispatch]
  );

  return { showNotification };
}; 