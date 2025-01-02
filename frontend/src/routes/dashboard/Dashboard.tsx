import React from 'react';
import { useAuth } from '../../contexts/auth';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Dashboard
          </h1>
        </div>
      </header>
      <main>
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <div className="border-4 border-dashed border-gray-200 rounded-lg h-96 p-4">
              <h2 className="text-lg font-medium text-gray-900">
                Bem-vindo, {user?.name}!
              </h2>
              <p className="mt-1 text-sm text-gray-500">
                Este é seu painel de controle.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}; 