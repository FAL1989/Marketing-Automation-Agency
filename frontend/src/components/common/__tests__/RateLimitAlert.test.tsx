import React from 'react';
import { render, screen } from '@testing-library/react';
import { RateLimitAlert } from '../RateLimitAlert';
import { ChakraProvider } from '@chakra-ui/react';

describe('RateLimitAlert', () => {
  const renderWithChakra = (ui: React.ReactElement) => {
    return render(
      <ChakraProvider>{ui}</ChakraProvider>
    );
  };

  it('displays remaining requests correctly', () => {
    renderWithChakra(
      <RateLimitAlert
        remainingRequests={50}
        maxRequests={100}
      />
    );

    expect(screen.getByText(/50 of 100 requests remaining/)).toBeInTheDocument();
  });

  it('shows warning state when requests are low', () => {
    renderWithChakra(
      <RateLimitAlert
        remainingRequests={5}
        maxRequests={100}
      />
    );

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '5');
  });

  it('shows blocked state correctly', () => {
    const resetTime = new Date();
    resetTime.setMinutes(resetTime.getMinutes() + 5);

    renderWithChakra(
      <RateLimitAlert
        remainingRequests={0}
        maxRequests={100}
        resetTime={resetTime}
        isBlocked={true}
      />
    );

    expect(screen.getByText(/Rate Limit Exceeded/)).toBeInTheDocument();
    expect(screen.getByText(/Reset in 5 minutes/)).toBeInTheDocument();
  });

  it('has correct ARIA attributes for accessibility', () => {
    renderWithChakra(
      <RateLimitAlert
        remainingRequests={50}
        maxRequests={100}
      />
    );

    const alert = screen.getByRole('alert');
    expect(alert).toHaveAttribute('aria-live', 'polite');

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuemin', '0');
    expect(progressBar).toHaveAttribute('aria-valuemax', '100');
    expect(progressBar).toHaveAttribute('aria-valuenow', '50');
  });

  it('changes ARIA live region based on blocked state', () => {
    const { rerender } = renderWithChakra(
      <RateLimitAlert
        remainingRequests={0}
        maxRequests={100}
        isBlocked={true}
      />
    );

    expect(screen.getByRole('alert')).toHaveAttribute('aria-live', 'assertive');

    rerender(
      <RateLimitAlert
        remainingRequests={50}
        maxRequests={100}
        isBlocked={false}
      />
    );

    expect(screen.getByRole('alert')).toHaveAttribute('aria-live', 'polite');
  });
}); 