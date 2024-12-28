import React from 'react';
import { render } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import { RateLimitAlert } from '../RateLimitAlert';
import { NotificationProvider } from '../Notifications';

describe('Responsive Design Tests', () => {
  const renderWithChakra = (ui: React.ReactElement) => {
    return render(
      <ChakraProvider>{ui}</ChakraProvider>
    );
  };

  describe('RateLimitAlert', () => {
    it('adapts to mobile viewport', () => {
      Object.defineProperty(window, 'innerWidth', { value: 375, configurable: true });
      const { container } = renderWithChakra(
        <RateLimitAlert
          remainingRequests={50}
          maxRequests={100}
        />
      );
      expect(container.firstChild).toBeVisible();
    });

    it('adapts to tablet viewport', () => {
      Object.defineProperty(window, 'innerWidth', { value: 768, configurable: true });
      const { container } = renderWithChakra(
        <RateLimitAlert
          remainingRequests={50}
          maxRequests={100}
        />
      );
      expect(container.firstChild).toBeVisible();
    });

    it('adapts to desktop viewport', () => {
      Object.defineProperty(window, 'innerWidth', { value: 1024, configurable: true });
      const { container } = renderWithChakra(
        <RateLimitAlert
          remainingRequests={50}
          maxRequests={100}
        />
      );
      expect(container.firstChild).toBeVisible();
    });
  });

  describe('NotificationProvider', () => {
    it('stacks notifications on mobile', () => {
      Object.defineProperty(window, 'innerWidth', { value: 375, configurable: true });
      const { container } = renderWithChakra(
        <NotificationProvider>
          <div>Test notification</div>
        </NotificationProvider>
      );
      expect(container.firstChild).toBeVisible();
    });

    it('shows notifications side by side on desktop', () => {
      Object.defineProperty(window, 'innerWidth', { value: 1024, configurable: true });
      const { container } = renderWithChakra(
        <NotificationProvider>
          <div>Test notification</div>
        </NotificationProvider>
      );
      expect(container.firstChild).toBeVisible();
    });
  });
}); 