import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { createBrowserRouter } from 'react-router-dom';
import { Layout } from './components/Layout';
import { HomePage } from './pages/HomePage';
import { TemplateListPage } from './pages/TemplateListPage';
import { TemplateEditorPage } from './pages/TemplateEditorPage';
import { ContentGeneratorPage } from './pages/ContentGeneratorPage';
import { GenerationHistoryPage } from './pages/GenerationHistoryPage';
import { PromptConfigPage } from './pages/PromptConfigPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { Login } from './pages/Login';
import { useAuth } from './hooks/useAuth';

const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  return user ? <>{children}</> : <Navigate to="/login" replace />;
};

const PrivateLayout = () => {
  return (
    <PrivateRoute>
      <Layout>
        <Outlet />
      </Layout>
    </PrivateRoute>
  );
};

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />
  },
  {
    path: '/',
    element: <PrivateLayout />,
    children: [
      {
        index: true,
        element: <HomePage />
      },
      {
        path: 'templates',
        element: <TemplateListPage />
      },
      {
        path: 'templates/:id',
        element: <TemplateEditorPage />
      },
      {
        path: 'generator',
        element: <ContentGeneratorPage />
      },
      {
        path: 'history',
        element: <GenerationHistoryPage />
      },
      {
        path: 'config',
        element: <PromptConfigPage />
      },
      {
        path: 'analytics',
        element: <AnalyticsPage />
      }
    ]
  }
]); 