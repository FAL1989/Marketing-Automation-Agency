import { renderHook } from '@testing-library/react';
import { toast } from 'react-toastify';
import { useNotification } from '../useNotification';
import { vi } from 'vitest';

vi.mock('react-toastify', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    warning: vi.fn(),
  },
}));

describe('useNotification', () => {
  const defaultToastOptions = {
    position: 'top-right',
    autoClose: 5000,
    hideProgressBar: false,
    closeOnClick: true,
    pauseOnHover: true,
    draggable: true,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('deve mostrar uma notificação de sucesso', () => {
    const { result } = renderHook(() => useNotification());
    const message = 'Operação realizada com sucesso';

    result.current.showSuccess(message);

    expect(toast.success).toHaveBeenCalledWith(message, defaultToastOptions);
  });

  it('deve mostrar uma notificação de erro', () => {
    const { result } = renderHook(() => useNotification());
    const message = 'Ocorreu um erro';

    result.current.showError(message);

    expect(toast.error).toHaveBeenCalledWith(message, defaultToastOptions);
  });

  it('deve mostrar uma notificação de aviso', () => {
    const { result } = renderHook(() => useNotification());
    const message = 'Atenção';

    result.current.showWarning(message);

    expect(toast.warning).toHaveBeenCalledWith(message, defaultToastOptions);
  });

  it('deve mostrar uma notificação de informação', () => {
    const { result } = renderHook(() => useNotification());
    const message = 'Informação importante';

    result.current.showInfo(message);

    expect(toast.info).toHaveBeenCalledWith(message, defaultToastOptions);
  });

  it('deve mostrar uma notificação genérica', () => {
    const { result } = renderHook(() => useNotification());
    const message = 'Mensagem genérica';

    result.current.showNotification(message);

    expect(toast.info).toHaveBeenCalledWith(message, defaultToastOptions);
  });

  it('deve mostrar uma notificação com tipo específico', () => {
    const { result } = renderHook(() => useNotification());
    const message = 'Mensagem personalizada';
    const type = 'warning';

    result.current.showNotification(message, type);

    expect(toast.warning).toHaveBeenCalledWith(message, defaultToastOptions);
  });

  it('deve usar o tipo info como padrão quando não especificado', () => {
    const { result } = renderHook(() => useNotification());
    const message = 'Mensagem sem tipo';

    result.current.showNotification(message);

    expect(toast.info).toHaveBeenCalledWith(message, defaultToastOptions);
    expect(toast.success).not.toHaveBeenCalled();
    expect(toast.error).not.toHaveBeenCalled();
    expect(toast.warning).not.toHaveBeenCalled();
  });
}); 