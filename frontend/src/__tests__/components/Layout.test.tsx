import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { Layout } from '../../components/Layout';
import { useAuth } from '../../hooks/useAuth';
import { User } from '../../types';

// Mock do hook useAuth
vi.mock('../../hooks/useAuth', () => ({
  useAuth: vi.fn()
}));

// Mock dos ícones do Heroicons
vi.mock('@heroicons/react/24/outline', () => ({
  HomeIcon: () => <span data-testid="home-icon">HomeIcon</span>,
  DocumentTextIcon: () => <span data-testid="document-icon">DocumentTextIcon</span>,
  ChartBarIcon: () => <span data-testid="chart-icon">ChartBarIcon</span>,
  UserIcon: () => <span data-testid="user-icon">UserIcon</span>,
  ArrowLeftOnRectangleIcon: () => <span data-testid="logout-icon">ArrowLeftOnRectangleIcon</span>
}));

describe('Layout', () => {
  const user = userEvent.setup({ delay: null });
  const mockSignOut = vi.fn();
  const mockUser: User = {
    id: '1',
    name: 'John Doe',
    email: 'john@example.com',
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-01')
  };

  beforeEach(() => {
    vi.mocked(useAuth).mockReturnValue({
      user: mockUser,
      signIn: vi.fn(),
      signOut: mockSignOut,
      loading: false,
      isAuthenticated: true
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  const renderLayout = (initialPath = '/dashboard') => {
    return render(
      <MemoryRouter initialEntries={[initialPath]}>
        <Layout>
          <div data-testid="child-content">Conteúdo filho</div>
        </Layout>
      </MemoryRouter>
    );
  };

  it('deve renderizar o título da aplicação', () => {
    renderLayout();
    expect(screen.getByText('AI Agency')).toBeInTheDocument();
  });

  it('deve renderizar todos os itens de navegação', () => {
    renderLayout();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Templates')).toBeInTheDocument();
    expect(screen.getByText('Analytics')).toBeInTheDocument();
  });

  it('deve renderizar o conteúdo filho', () => {
    renderLayout();
    expect(screen.getByTestId('child-content')).toBeInTheDocument();
    expect(screen.getByText('Conteúdo filho')).toBeInTheDocument();
  });

  it('deve exibir o nome do usuário', () => {
    renderLayout();
    expect(screen.getByText(mockUser.name)).toBeInTheDocument();
  });

  it('deve chamar signOut ao clicar no botão de sair', async () => {
    renderLayout();
    const logoutButton = screen.getByRole('button', { name: /sair/i });
    await user.click(logoutButton);
    await waitFor(() => {
      expect(mockSignOut).toHaveBeenCalled();
    });
  });

  it('deve aplicar classes corretas ao item de navegação ativo', () => {
    renderLayout('/templates');
    const dashboardLink = screen.getByText('Dashboard').closest('a');
    const templatesLink = screen.getByText('Templates').closest('a');

    expect(dashboardLink).toHaveClass('text-white', 'hover:bg-indigo-600');
    expect(templatesLink).toHaveClass('bg-indigo-800', 'text-white');
  });

  it('deve renderizar todos os ícones corretamente', () => {
    renderLayout();
    expect(screen.getByTestId('home-icon')).toBeInTheDocument();
    expect(screen.getByTestId('document-icon')).toBeInTheDocument();
    expect(screen.getByTestId('chart-icon')).toBeInTheDocument();
    expect(screen.getByTestId('user-icon')).toBeInTheDocument();
    expect(screen.getByTestId('logout-icon')).toBeInTheDocument();
  });

  it('deve ter a estrutura correta do layout', () => {
    renderLayout();
    
    // Verifica o container principal
    const mainContainer = screen.getByRole('main');
    expect(mainContainer).toHaveClass('flex-1');
    
    // Verifica a sidebar
    const sidebar = screen.getByRole('navigation');
    expect(sidebar).toHaveClass('mt-5', 'flex-1', 'px-2', 'space-y-1');
    
    // Verifica a área de conteúdo
    const content = screen.getByTestId('child-content').parentElement;
    expect(content).toHaveClass('max-w-7xl', 'mx-auto', 'px-4', 'sm:px-6', 'md:px-8');
  });

  it('deve ter os estilos corretos para o perfil do usuário', () => {
    renderLayout();
    
    const userProfile = screen.getByText(mockUser.name).closest('.group');
    expect(userProfile).toHaveClass('flex-shrink-0', 'w-full', 'group', 'block');
    
    const userContainer = screen.getByText(mockUser.name).closest('.flex');
    expect(userContainer).toHaveClass('flex', 'items-center');
    
    const userName = screen.getByText(mockUser.name);
    expect(userName).toHaveClass('text-sm', 'font-medium', 'text-white');
  });
}); 