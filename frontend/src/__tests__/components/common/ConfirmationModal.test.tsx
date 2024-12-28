import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { ConfirmationModal } from '../../../components/common/ConfirmationModal';

// Mock dos ícones do Heroicons
vi.mock('@heroicons/react/24/outline', () => ({
  ExclamationTriangleIcon: () => <span data-testid="warning-icon">ExclamationTriangleIcon</span>,
  InformationCircleIcon: () => <span data-testid="info-icon">InformationCircleIcon</span>
}));

describe('ConfirmationModal', () => {
  const user = userEvent.setup({ delay: null });
  
  const defaultProps = {
    isOpen: true,
    title: 'Título do Modal',
    message: 'Mensagem de confirmação',
    onConfirm: vi.fn(),
    onCancel: vi.fn()
  };

  const renderModal = (props = {}) => {
    return render(
      <ConfirmationModal
        {...defaultProps}
        {...props}
      />
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('deve renderizar o modal com título e mensagem', () => {
    renderModal();
    
    expect(screen.getByText('Título do Modal')).toBeInTheDocument();
    expect(screen.getByText('Mensagem de confirmação')).toBeInTheDocument();
  });

  it('deve renderizar botões com texto padrão', () => {
    renderModal();
    
    expect(screen.getByText('Confirmar')).toBeInTheDocument();
    expect(screen.getByText('Cancelar')).toBeInTheDocument();
  });

  it('deve renderizar botões com texto personalizado', () => {
    renderModal({
      confirmText: 'Sim, excluir',
      cancelText: 'Não, manter'
    });
    
    expect(screen.getByText('Sim, excluir')).toBeInTheDocument();
    expect(screen.getByText('Não, manter')).toBeInTheDocument();
  });

  it('deve chamar onConfirm ao clicar no botão de confirmação', async () => {
    const onConfirm = vi.fn();
    renderModal({ onConfirm });
    
    await user.click(screen.getByText('Confirmar'));
    
    await waitFor(() => {
      expect(onConfirm).toHaveBeenCalled();
    });
  });

  it('deve chamar onCancel ao clicar no botão de cancelar', async () => {
    const onCancel = vi.fn();
    renderModal({ onCancel });
    
    await user.click(screen.getByText('Cancelar'));
    
    await waitFor(() => {
      expect(onCancel).toHaveBeenCalled();
    });
  });

  it('deve renderizar o ícone correto para cada tipo', () => {
    // Tipo danger
    const { unmount: unmountDanger } = renderModal({ type: 'danger' });
    expect(screen.getByTestId('warning-icon')).toBeInTheDocument();
    unmountDanger();
    
    // Tipo warning
    const { unmount: unmountWarning } = renderModal({ type: 'warning' });
    expect(screen.getByTestId('warning-icon')).toBeInTheDocument();
    unmountWarning();
    
    // Tipo info
    const { unmount: unmountInfo } = renderModal({ type: 'info' });
    expect(screen.getByTestId('info-icon')).toBeInTheDocument();
    unmountInfo();
  });

  it('deve aplicar as cores corretas para cada tipo', () => {
    // Tipo danger
    const { unmount: unmountDanger } = renderModal({ type: 'danger' });
    const dangerIcon = screen.getByTestId('warning-icon').closest('div');
    expect(dangerIcon).toHaveClass('bg-red-100');
    unmountDanger();
    
    // Tipo warning
    const { unmount: unmountWarning } = renderModal({ type: 'warning' });
    const warningIcon = screen.getByTestId('warning-icon').closest('div');
    expect(warningIcon).toHaveClass('bg-yellow-100');
    unmountWarning();
    
    // Tipo info
    const { unmount: unmountInfo } = renderModal({ type: 'info' });
    const infoIcon = screen.getByTestId('info-icon').closest('div');
    expect(infoIcon).toHaveClass('bg-blue-100');
    unmountInfo();
  });

  it('deve renderizar campo de confirmação quando fornecido', () => {
    renderModal({
      confirmationInput: {
        label: 'Digite "excluir" para confirmar',
        value: 'excluir'
      }
    });
    
    expect(screen.getByLabelText('Digite "excluir" para confirmar')).toBeInTheDocument();
  });

  it('deve desabilitar botão de confirmar quando input não corresponde', async () => {
    renderModal({
      confirmationInput: {
        label: 'Digite "excluir" para confirmar',
        value: 'excluir'
      }
    });
    
    const confirmButton = screen.getByText('Confirmar');
    const input = screen.getByLabelText('Digite "excluir" para confirmar');
    
    expect(confirmButton).toBeDisabled();
    
    await user.type(input, 'exclu');
    expect(confirmButton).toBeDisabled();
    
    await user.clear(input);
    await user.type(input, 'excluir');
    expect(confirmButton).not.toBeDisabled();
  });

  it('deve ter os estilos corretos nos elementos principais', () => {
    renderModal();
    
    // Verifica o overlay
    const overlay = document.querySelector('.fixed.inset-0.bg-gray-500.bg-opacity-75');
    expect(overlay).toBeInTheDocument();
    
    // Verifica o container do modal
    const modalContainer = document.querySelector('.fixed.inset-0.z-10.overflow-y-auto');
    expect(modalContainer).toBeInTheDocument();
    
    // Verifica o painel do modal
    const modalPanel = document.querySelector('.relative.transform.overflow-hidden.rounded-lg.bg-white');
    expect(modalPanel).toBeInTheDocument();
    
    // Verifica o título
    const title = screen.getByRole('heading', { name: 'Título do Modal' });
    expect(title).toHaveClass('text-base', 'font-semibold', 'leading-6', 'text-gray-900');
    
    // Verifica a mensagem
    const message = screen.getByText('Mensagem de confirmação');
    expect(message).toHaveClass('text-sm', 'text-gray-500');
    
    // Verifica os botões
    const confirmButton = screen.getByRole('button', { name: 'Confirmar' });
    expect(confirmButton).toHaveClass(
      'inline-flex',
      'w-full',
      'justify-center',
      'rounded-md',
      'px-3',
      'py-2',
      'text-sm',
      'font-semibold',
      'text-white',
      'shadow-sm',
      'sm:ml-3',
      'sm:w-auto'
    );
    
    const cancelButton = screen.getByRole('button', { name: 'Cancelar' });
    expect(cancelButton).toHaveClass(
      'mt-3',
      'inline-flex',
      'w-full',
      'justify-center',
      'rounded-md',
      'bg-white',
      'px-3',
      'py-2',
      'text-sm',
      'font-semibold',
      'text-gray-900',
      'shadow-sm',
      'ring-1',
      'ring-inset',
      'ring-gray-300',
      'hover:bg-gray-50',
      'sm:mt-0',
      'sm:w-auto'
    );
  });
}); 