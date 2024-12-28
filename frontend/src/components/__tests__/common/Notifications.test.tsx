import { render, screen, act } from '@testing-library/react';
import { NotificationProvider, useNotification } from '../../../contexts/NotificationContext';
import { vi } from 'vitest';

describe('Notifications', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it('deve mostrar e esconder a notificação', async () => {
    const TestComponent = () => {
      const { showNotification, notifications } = useNotification();
      return (
        <>
          <button onClick={() => showNotification('success', 'Teste', '3000')}>
            Mostrar Notificação
          </button>
          <div role="alert">
            {notifications.map(notification => (
              <div key={notification.id}>{notification.message}</div>
            ))}
          </div>
        </>
      );
    };

    render(
      <NotificationProvider>
        <TestComponent />
      </NotificationProvider>
    );

    const button = screen.getByText('Mostrar Notificação');
    
    await act(async () => {
      button.click();
    });

    expect(screen.getByText('Teste')).toBeInTheDocument();

    await act(async () => {
      vi.runAllTimers();
    });

    expect(screen.queryByText('Teste')).not.toBeInTheDocument();
  });
}); 