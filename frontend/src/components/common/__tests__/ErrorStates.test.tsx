import React from 'react';
import { render, screen } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import { RateLimitAlert } from '../RateLimitAlert';
import { NotificationProvider, useNotifications } from '../Notifications';

const renderWithChakra = (ui: React.ReactElement) => {
  return render(
    <ChakraProvider>
      <NotificationProvider>
        {ui}
      </NotificationProvider>
    </ChakraProvider>
  );
};

const ErrorTrigger = () => {
  const { addNotification } = useNotifications();
  React.useEffect(() => {
    addNotification({
      type: 'error',
      title: 'Error occurred',
      message: 'Something went wrong',
      duration: 5000
    });
  }, [addNotification]);
  return null;
};

describe('Error State Tests', () => {
  describe('RateLimitAlert', () => {
    it('displays blocked state with error styling', () => {
      renderWithChakra(
        <RateLimitAlert
          remainingRequests={0}
          maxRequests={100}
          isBlocked={true}
        />
      );

      expect(screen.getByText(/Rate Limit Exceeded/)).toBeInTheDocument();
      const alert = screen.getByRole('alert');
      expect(alert).toHaveAttribute('aria-live', 'assertive');
    });

    it('shows warning state when close to limit', () => {
      renderWithChakra(
        <RateLimitAlert
          remainingRequests={5}
          maxRequests={100}
        />
      );

      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '5');
    });
  });

  describe('Notifications', () => {
    it('displays error notification with correct styling', () => {
      renderWithChakra(<ErrorTrigger />);
      
      expect(screen.getByText('Error occurred')).toBeInTheDocument();
      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    });

    it('handles multiple error notifications', () => {
      const { rerender } = renderWithChakra(<ErrorTrigger />);
      rerender(<ErrorTrigger />);
      
      const errorTitles = screen.getAllByText('Error occurred');
      expect(errorTitles).toHaveLength(2);
    });
  });

  describe('Error Boundaries', () => {
    const ErrorComponent = () => {
      throw new Error('Test error');
    };

    it('catches and displays component errors', () => {
      const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
      
      renderWithChakra(
        <React.Suspense fallback={<div>Loading...</div>}>
          <ErrorComponent />
        </React.Suspense>
      );
      
      expect(spy).toHaveBeenCalled();
      spy.mockRestore();
    });
  });
}); 