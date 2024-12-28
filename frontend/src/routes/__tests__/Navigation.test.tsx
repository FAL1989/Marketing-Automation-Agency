import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ChakraProvider } from '@chakra-ui/react';
import { AppRoutes } from '../index';
import { AuthProvider } from '../../contexts/AuthContext';

const renderWithProviders = (ui: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <ChakraProvider>
        <AuthProvider>
          {ui}
        </AuthProvider>
      </ChakraProvider>
    </BrowserRouter>
  );
};

describe('Navigation Tests', () => {
  beforeEach(() => {
    // Mock localStorage para simular autenticação
    Storage.prototype.getItem = jest.fn(() => 'fake-token');
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('redirects to login when not authenticated', () => {
    Storage.prototype.getItem = jest.fn(() => null);
    renderWithProviders(<AppRoutes />);
    expect(window.location.pathname).toBe('/login');
  });

  it('navigates to dashboard when authenticated', () => {
    renderWithProviders(<AppRoutes />);
    expect(window.location.pathname).toBe('/');
  });

  it('navigates to templates page', () => {
    renderWithProviders(<AppRoutes />);
    const templatesLink = screen.getByText(/templates/i);
    fireEvent.click(templatesLink);
    expect(window.location.pathname).toBe('/templates');
  });

  it('navigates to analytics page', () => {
    renderWithProviders(<AppRoutes />);
    const analyticsLink = screen.getByText(/analytics/i);
    fireEvent.click(analyticsLink);
    expect(window.location.pathname).toBe('/analytics');
  });

  it('maintains authentication state during navigation', () => {
    renderWithProviders(<AppRoutes />);
    const analyticsLink = screen.getByText(/analytics/i);
    const templatesLink = screen.getByText(/templates/i);
    
    fireEvent.click(analyticsLink);
    expect(window.location.pathname).toBe('/analytics');
    
    fireEvent.click(templatesLink);
    expect(window.location.pathname).toBe('/templates');
    expect(Storage.prototype.getItem).toHaveBeenCalledWith('token');
  });
}); 