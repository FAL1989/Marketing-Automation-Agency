import React from 'react';
import { Generation } from '../types';
import { CheckCircleIcon, XCircleIcon, ClockIcon } from '@heroicons/react/24/outline';
import { formatDate } from '../utils/dateUtils';

interface GenerationHistoryProps {
  generations: Generation[];
  onSelect: (generation: Generation) => void;
}

export const GenerationHistory: React.FC<GenerationHistoryProps> = ({
  generations,
  onSelect,
}) => {
  if (generations.length === 0) {
    return (
      <div className="text-center py-6">
        <p className="text-gray-500">Nenhuma geração encontrada.</p>
      </div>
    );
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
      case 'success':
        return <CheckCircleIcon data-testid="check-circle-icon" className="h-5 w-5 text-green-500" />;
      case 'failed':
      case 'error':
        return <XCircleIcon data-testid="x-circle-icon" className="h-5 w-5 text-red-500" />;
      default:
        return <ClockIcon data-testid="clock-icon" className="h-5 w-5 text-yellow-500" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
      case 'success':
        return 'Sucesso';
      case 'failed':
      case 'error':
        return 'Erro';
      default:
        return 'Em Progresso';
    }
  };

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'completed':
      case 'success':
        return 'bg-green-100 text-green-800';
      case 'failed':
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  return (
    <div className="flow-root">
      <ul role="list" className="-my-5 divide-y divide-gray-200">
        {generations.map((generation) => (
          <li
            key={generation.id}
            className="py-4 cursor-pointer hover:bg-gray-50"
            onClick={() => onSelect(generation)}
          >
            <div className="flex items-center space-x-4">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {generation.status === 'pending' ? 'Aguardando geração...' : `${generation.content?.substring(0, 10)}...`}
                </p>
                <p className="text-sm text-gray-500">
                  {formatDate(generation.createdAt)}
                </p>
              </div>
              <div>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusClass(generation.status)}`}>
                  {getStatusIcon(generation.status)}
                  <span className="ml-1">{getStatusText(generation.status)}</span>
                </span>
              </div>
            </div>
            {generation.error && (
              <p className="mt-1 text-sm text-red-600">{generation.error}</p>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}; 