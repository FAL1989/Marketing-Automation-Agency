import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { Sidebar } from '../../components/Sidebar';

// Mock dos ícones do Heroicons
vi.mock('@heroicons/react/24/outline', () => ({
  HomeIcon: () => <span data-testid="home-icon">HomeIcon</span>,
  DocumentDuplicateIcon: () => <span data-testid="template-icon">DocumentDuplicateIcon</span>,
  ChartBarIcon: () => <span data-testid="analytics-icon">ChartBarIcon</span>,
  Cog6ToothIcon: () => <span data-testid="settings-icon">Cog6ToothIcon</span>
}));

describe('Sidebar', () => {
  const renderSidebar = (initialRoute = '/') => {
    return render(
      <MemoryRouter initialEntries={[initialRoute]}>
        <Sidebar />
      </MemoryRouter>
    );
  };

  it('deve renderizar todos os itens de navegação', () => {
    renderSidebar();
    
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Templates')).toBeInTheDocument();
    expect(screen.getByText('Analytics')).toBeInTheDocument();
    expect(screen.getByText('Configurações')).toBeInTheDocument();
  });

  it('deve renderizar todos os ícones corretamente', () => {
    renderSidebar();
    
    expect(screen.getByTestId('home-icon')).toBeInTheDocument();
    expect(screen.getByTestId('template-icon')).toBeInTheDocument();
    expect(screen.getByTestId('analytics-icon')).toBeInTheDocument();
    expect(screen.getByTestId('settings-icon')).toBeInTheDocument();
  });

  it('deve aplicar classes corretas ao item ativo', () => {
    renderSidebar('/templates');
    
    const templateLink = screen.getByText('Templates').closest('a');
    expect(templateLink).toHaveClass('bg-gray-100', 'text-gray-900');
    
    const dashboardLink = screen.getByText('Dashboard').closest('a');
    expect(dashboardLink).toHaveClass('text-gray-600', 'hover:bg-gray-50', 'hover:text-gray-900');
  });

  it('deve ter os links corretos para cada item', () => {
    renderSidebar();
    
    expect(screen.getByText('Dashboard').closest('a')).toHaveAttribute('href', '/');
    expect(screen.getByText('Templates').closest('a')).toHaveAttribute('href', '/templates');
    expect(screen.getByText('Analytics').closest('a')).toHaveAttribute('href', '/analytics');
    expect(screen.getByText('Configurações').closest('a')).toHaveAttribute('href', '/settings');
  });

  it('deve ter as classes base corretas para o container', () => {
    renderSidebar();
    
    const container = screen.getByRole('navigation').parentElement?.parentElement;
    expect(container).toHaveClass('flex', 'flex-col', 'flex-grow', 'pt-5', 'bg-white', 'overflow-y-auto');
    
    const nav = screen.getByRole('navigation');
    expect(nav).toHaveClass('flex-1', 'px-2', 'pb-4', 'space-y-1');
  });

  it('deve ter as classes corretas para os ícones inativos', () => {
    renderSidebar('/templates');
    
    const homeIcon = screen.getByTestId('home-icon').parentElement;
    expect(homeIcon).toHaveClass('text-gray-600', 'hover:bg-gray-50', 'hover:text-gray-900', 'group', 'flex', 'items-center', 'px-2', 'py-2', 'text-sm', 'font-medium', 'rounded-md');
  });
}); 