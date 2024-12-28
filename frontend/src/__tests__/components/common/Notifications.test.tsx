import { render, screen, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import userEvent from '@testing-library/user-event';
import { NotificationProvider, useNotifications } from '../../../components/common/Notifications';

// Mock dos ícones do Heroicons
vi.mock('@heroicons/react/24/outline', () => ({
  CheckCircleIcon: () => <span data-testid="success-icon">CheckCircleIcon</span>,
  XCircleIcon: () => <span data-testid="error-icon">XCircleIcon</span>,
  ExclamationCircleIcon: () => <span data-testid="warning-icon">ExclamationCircleIcon</span>,
  InformationCircleIcon: () => <span data-testid="info-icon">InformationCircleIcon</span>,
  XMarkIcon: () => <span data-testid="close-icon">XMarkIcon</span>
}));

// Componente de teste para usar o hook
const TestComponent = ({ actionMock = vi.fn() }) => {
  const { show, clear } = useNotifications();

  return (
    <div>
      <button onClick={() => show({
        type: 'success',
        title: 'Sucesso',
        message: 'Operação realizada com sucesso',
        duration: 5000
      })}>
        Mostrar Sucesso
      </button>
      <button onClick={() => show({
        type: 'error',
        title: 'Erro',
        message: 'Algo deu errado',
        duration: 5000
      })}>
        Mostrar Erro
      </button>
      <button onClick={() => show({
        type: 'warning',
        title: 'Aviso',
        message: 'Atenção necessária',
        duration: 5000,
        actions: [
          {
            label: 'Ação',
            onClick: actionMock
          }
        ]
      })}>
        Mostrar Aviso
      </button>
      <button onClick={() => show({
        type: 'info',
        title: 'Informação',
        message: 'Apenas informando',
        duration: 0
      })}>
        Mostrar Info
      </button>
      <button onClick={clear}>Limpar</button>
    </div>
  );
};

describe('Notifications', () => {
  const user = userEvent.setup({ delay: null });

  const renderNotifications = (actionMock = vi.fn()) => {
    return render(
      <NotificationProvider>
        <TestComponent actionMock={actionMock} />
      </NotificationProvider>
    );
  };

  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.clearAllTimers();
    vi.useRealTimers();
  });

  it('deve mostrar notificação de sucesso', async () => {
    renderNotifications();
    
    await user.click(screen.getByText('Mostrar Sucesso'));
    
    expect(screen.getByTestId('success-icon')).toBeInTheDocument();
    expect(screen.getByText('Sucesso')).toBeInTheDocument();
    expect(screen.getByText('Operação realizada com sucesso')).toBeInTheDocument();
  });

  it('deve mostrar notificação de erro', async () => {
    renderNotifications();
    
    await user.click(screen.getByText('Mostrar Erro'));
    
    expect(screen.getByTestId('error-icon')).toBeInTheDocument();
    expect(screen.getByText('Erro')).toBeInTheDocument();
    expect(screen.getByText('Algo deu errado')).toBeInTheDocument();
  });

  it('deve mostrar notificação com ações', async () => {
    renderNotifications();
    
    await user.click(screen.getByText('Mostrar Aviso'));
    
    expect(screen.getByTestId('warning-icon')).toBeInTheDocument();
    expect(screen.getByText('Aviso')).toBeInTheDocument();
    expect(screen.getByText('Atenção necessária')).toBeInTheDocument();
    expect(screen.getByText('Ação')).toBeInTheDocument();
  });

  it('deve remover notificação ao clicar no botão fechar', async () => {
    renderNotifications();
    
    await user.click(screen.getByText('Mostrar Info'));
    
    expect(screen.getByText('Informação')).toBeInTheDocument();
    
    await user.click(screen.getByTestId('close-icon'));
    
    await waitFor(() => {
      expect(screen.queryByText('Informação')).not.toBeInTheDocument();
    });
  });

  it('deve remover notificação automaticamente após o tempo definido', async () => {
    renderNotifications();
    
    await user.click(screen.getByText('Mostrar Sucesso'));
    
    expect(screen.getByText('Sucesso')).toBeInTheDocument();
    
    await act(async () => {
      vi.advanceTimersByTime(5000);
    });
    
    await waitFor(() => {
      expect(screen.queryByText('Sucesso')).not.toBeInTheDocument();
    });
  });

  it('não deve remover notificação automaticamente se duration for 0', async () => {
    renderNotifications();
    
    await user.click(screen.getByText('Mostrar Info'));
    
    expect(screen.getByText('Informação')).toBeInTheDocument();
    
    await act(async () => {
      vi.advanceTimersByTime(5000);
    });
    
    expect(screen.getByText('Informação')).toBeInTheDocument();
  });

  it('deve limpar todas as notificações', async () => {
    renderNotifications();
    
    await user.click(screen.getByText('Mostrar Sucesso'));
    await user.click(screen.getByText('Mostrar Erro'));
    await user.click(screen.getByText('Mostrar Info'));
    
    expect(screen.getByText('Sucesso')).toBeInTheDocument();
    expect(screen.getByText('Erro')).toBeInTheDocument();
    expect(screen.getByText('Informação')).toBeInTheDocument();
    
    await user.click(screen.getByText('Limpar'));
    
    await waitFor(() => {
      expect(screen.queryByText('Sucesso')).not.toBeInTheDocument();
      expect(screen.queryByText('Erro')).not.toBeInTheDocument();
      expect(screen.queryByText('Informação')).not.toBeInTheDocument();
    });
  });

  it('deve executar a ação e fechar a notificação ao clicar no botão de ação', async () => {
    const actionMock = vi.fn();
    renderNotifications(actionMock);
    
    await user.click(screen.getByText('Mostrar Aviso'));
    
    expect(screen.getByText('Aviso')).toBeInTheDocument();
    
    const actionButton = screen.getByText('Ação');
    await user.click(actionButton);
    
    expect(actionMock).toHaveBeenCalled();
    await waitFor(() => {
      expect(screen.queryByText('Aviso')).not.toBeInTheDocument();
    });
  });

  it('deve ter os estilos corretos nos elementos principais', async () => {
    const { container } = renderNotifications();
    
    await user.click(screen.getByText('Mostrar Sucesso'));
    
    // Container principal
    const notificationContainer = container.querySelector('[aria-live="assertive"]') as HTMLElement;
    expect(notificationContainer).toHaveClass('pointer-events-none', 'fixed', 'inset-0', 'flex', 'items-end', 'px-4', 'py-6', 'sm:items-start', 'sm:p-6', 'z-50');
    
    // Container das notificações
    const notificationsWrapper = notificationContainer.firstElementChild as HTMLElement;
    expect(notificationsWrapper).toHaveClass('flex', 'w-full', 'flex-col', 'items-center', 'space-y-4', 'sm:items-end');
    
    // Container da notificação
    const notification = screen.getByText('Sucesso').closest('.bg-white') as HTMLElement;
    expect(notification).toHaveClass(
      'pointer-events-auto',
      'w-full',
      'max-w-sm',
      'overflow-hidden',
      'rounded-lg',
      'bg-white',
      'shadow-lg',
      'ring-1',
      'ring-black',
      'ring-opacity-5'
    );
    
    // Container do conteúdo
    const contentContainer = screen.getByText('Sucesso').closest('.flex.items-start') as HTMLElement;
    expect(contentContainer).toHaveClass('flex', 'items-start');
    
    // Ícone
    const icon = screen.getByTestId('success-icon').parentElement as HTMLElement;
    expect(icon).toHaveClass('flex-shrink-0');
    
    // Container do texto
    const textContainer = screen.getByText('Sucesso').parentElement as HTMLElement;
    expect(textContainer).toHaveClass('ml-3', 'w-0', 'flex-1', 'pt-0.5');
    
    // Título
    const title = screen.getByText('Sucesso');
    expect(title).toHaveClass('text-sm', 'font-medium', 'text-gray-900');
    
    // Mensagem
    const message = screen.getByText('Operação realizada com sucesso');
    expect(message).toHaveClass('mt-1', 'text-sm', 'text-gray-500');
    
    // Botão de fechar
    const closeButton = screen.getByRole('button', { name: /fechar/i });
    expect(closeButton).toHaveClass(
      'inline-flex',
      'rounded-md',
      'bg-white',
      'text-gray-400',
      'hover:text-gray-500',
      'focus:outline-none',
      'focus:ring-2',
      'focus:ring-indigo-500',
      'focus:ring-offset-2'
    );
  });
}); 