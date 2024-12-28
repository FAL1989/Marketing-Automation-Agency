import React, { useState } from 'react';
import { MetricCard } from './MetricCard';
import { useAnalytics } from '../hooks/useAnalytics';
import { useNotification } from '../hooks/useNotification';
import { Generation } from '../types';

type SortOption = 'date-asc' | 'date-desc';
type StatusFilter = 'all' | 'success' | 'error' | 'pending';

export const Dashboard: React.FC = () => {
  const { metrics, isLoading, error, refreshMetrics } = useAnalytics();
  const { showInfo } = useNotification();
  const [sortBy, setSortBy] = useState<SortOption>('date-desc');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [selectedGeneration, setSelectedGeneration] = useState<Generation | null>(null);

  const handleRefresh = async () => {
    showInfo('Atualizando métricas...');
    await refreshMetrics();
  };

  const filteredGenerations = metrics?.recentGenerations.filter(gen => 
    statusFilter === 'all' || gen.status === statusFilter
  ) || [];

  const sortedGenerations = [...filteredGenerations].sort((a, b) => {
    const dateA = new Date(a.createdAt).getTime();
    const dateB = new Date(b.createdAt).getTime();
    return sortBy === 'date-desc' ? dateB - dateA : dateA - dateB;
  });

  if (isLoading) {
    return (
      <div data-testid="loading-state" className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 p-4 rounded-md">
        <div className="text-red-700">
          Falha ao carregar métricas: {error.message}
        </div>
      </div>
    );
  }

  if (!metrics) {
    return null;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <button
          onClick={handleRefresh}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Atualizar
        </button>
      </div>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Total de Gerações"
          value={metrics.totalGenerations}
          icon="chart-bar"
        />
        <MetricCard
          title="Taxa de Sucesso"
          value={`${metrics.successRate}%`}
          icon="check-circle"
        />
        <MetricCard
          title="Tempo Médio"
          value={`${metrics.averageTime}s`}
          icon="clock"
        />
        <MetricCard
          title="Templates Ativos"
          value={metrics.activeTemplates}
          icon="template"
        />
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-medium text-gray-900">Gerações Recentes</h2>
          <div className="flex gap-4">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
              className="rounded-md border-gray-300"
              aria-label="Filtrar por status"
            >
              <option value="all">Todos os status</option>
              <option value="success">Sucesso</option>
              <option value="error">Erro</option>
              <option value="pending">Pendente</option>
            </select>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
              className="rounded-md border-gray-300"
              aria-label="Ordenar por"
            >
              <option value="date-desc">Mais recentes primeiro</option>
              <option value="date-asc">Mais antigos primeiro</option>
            </select>
          </div>
        </div>

        <div className="space-y-4">
          {sortedGenerations.map((generation) => (
            <div
              key={generation.id}
              onClick={() => setSelectedGeneration(generation)}
              className="p-4 border rounded-md hover:bg-gray-50 cursor-pointer"
            >
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="font-medium text-gray-900">{generation.content}</h3>
                  <p className="text-sm text-gray-500">
                    Template: {metrics.popularTemplates.find(t => t.templateId === generation.templateId)?.name}
                  </p>
                </div>
                <div className={`px-2 py-1 rounded-full text-sm ${
                  generation.status === 'success' ? 'bg-green-100 text-green-800' :
                  generation.status === 'error' ? 'bg-red-100 text-red-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {generation.status}
                </div>
              </div>
              {selectedGeneration?.id === generation.id && (
                <div className="mt-4 p-4 bg-gray-50 rounded-md">
                  <h4 className="font-medium mb-2">Parâmetros:</h4>
                  <pre className="text-sm">
                    {Object.entries(generation.parameters).map(([key, value]) => (
                      <div key={key}>{key}: {value}</div>
                    ))}
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}; 