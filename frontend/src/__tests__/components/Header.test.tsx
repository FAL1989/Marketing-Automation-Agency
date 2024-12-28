import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { Header } from '../../components/Header';

const mockSignOut = vi.fn();

// Mock do hook de autenticação
vi.mock('../../hooks/useAuth', () => ({
  useAuth: () => ({
    user: {
      id: '1',
      name: 'João Silva',
      email: 'joao@exemplo.com',
      createdAt: new Date('2024-01-01'),
      updatedAt: new Date('2024-01-01')
    },
    loading: false,
    isAuthenticated: true,
    signIn: vi.fn(),
    signOut: mockSignOut
  })
}));

describe('Header', () => {
  const renderHeader = () => {
    return render(
      <BrowserRouter>
        <Header />
      </BrowserRouter>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('deve renderizar o título corretamente', () => {
    renderHeader();
    const title = screen.getByText('AI Content Generator');
    expect(title).toBeInTheDocument();
    expect(title.tagName.toLowerCase()).toBe('a');
    expect(title).toHaveAttribute('href', '/');
  });

  it('deve exibir o nome do usuário', () => {
    renderHeader();
    expect(screen.getByText('João Silva')).toBeInTheDocument();
  });

  it('deve chamar a função signOut ao clicar no botão de sair', async () => {
    renderHeader();
    
    const logoutButton = screen.getByText('Sair');
    await userEvent.click(logoutButton);
    
    expect(mockSignOut).toHaveBeenCalled();
  });

  it('deve ter os estilos corretos nos elementos principais', () => {
    renderHeader();
    
    const header = screen.getByRole('banner');
    expect(header).toHaveClass('bg-white', 'shadow');
    
    const title = screen.getByText('AI Content Generator');
    expect(title).toHaveClass('text-xl', 'font-bold', 'text-indigo-600');
    
    const logoutButton = screen.getByText('Sair');
    expect(logoutButton).toHaveClass(
      'inline-flex',
      'items-center',
      'px-3',
      'py-2',
      'border',
      'border-transparent',
      'text-sm',
      'rounded-md'
    );
  });
}); 