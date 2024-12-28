import React, { useState } from 'react';
import { ClockIcon, ArrowPathIcon, DocumentDuplicateIcon } from '@heroicons/react/24/outline';

interface TemplateVersion {
  id: string;
  version: number;
  createdAt: Date;
  createdBy: string;
  changes: string[];
  snapshot: any; // Snapshot completo do template naquela versão
}

interface VersionHistoryProps {
  versions: TemplateVersion[];
  onRevert: (version: TemplateVersion) => Promise<void>;
  onCompare: (version1: TemplateVersion, version2: TemplateVersion) => void;
}

export const VersionHistory: React.FC<VersionHistoryProps> = ({
  versions,
  onRevert,
  onCompare
}) => {
  const [selectedVersions, setSelectedVersions] = useState<string[]>([]);
  const [loading, setLoading] = useState<string | null>(null);

  const handleVersionSelect = (versionId: string) => {
    setSelectedVersions(prev => {
      if (prev.includes(versionId)) {
        return prev.filter(id => id !== versionId);
      }
      if (prev.length >= 2) {
        return [prev[1], versionId];
      }
      return [...prev, versionId];
    });
  };

  const handleRevert = async (version: TemplateVersion) => {
    try {
      setLoading(version.id);
      await onRevert(version);
    } catch (error) {
      console.error('Erro ao reverter versão:', error);
    } finally {
      setLoading(null);
    }
  };

  const handleCompare = () => {
    if (selectedVersions.length !== 2) return;
    
    const [version1, version2] = selectedVersions.map(
      id => versions.find(v => v.id === id)!
    );
    
    onCompare(version1, version2);
  };

  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(new Date(date));
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium text-gray-900">Histórico de Versões</h3>
        {selectedVersions.length === 2 && (
          <button
            onClick={handleCompare}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700"
          >
            <DocumentDuplicateIcon className="h-5 w-5 mr-2" />
            Comparar Versões
          </button>
        )}
      </div>

      <div className="space-y-4">
        {versions.map((version) => (
          <div
            key={version.id}
            className={`bg-white shadow-sm rounded-lg p-4 border-2 ${
              selectedVersions.includes(version.id)
                ? 'border-indigo-500'
                : 'border-transparent'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={selectedVersions.includes(version.id)}
                  onChange={() => handleVersionSelect(version.id)}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <div>
                  <h4 className="text-sm font-medium text-gray-900">
                    Versão {version.version}
                  </h4>
                  <div className="mt-1 flex items-center text-sm text-gray-500">
                    <ClockIcon className="h-4 w-4 mr-1" />
                    {formatDate(version.createdAt)}
                  </div>
                  <div className="mt-1 text-sm text-gray-500">
                    por {version.createdBy}
                  </div>
                </div>
              </div>

              <button
                onClick={() => handleRevert(version)}
                disabled={loading === version.id}
                className={`inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 ${
                  loading === version.id ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                <ArrowPathIcon className="h-5 w-5 mr-2" />
                {loading === version.id ? 'Revertendo...' : 'Reverter'}
              </button>
            </div>

            {version.changes.length > 0 && (
              <div className="mt-3">
                <h5 className="text-sm font-medium text-gray-900 mb-2">
                  Alterações:
                </h5>
                <ul className="list-disc pl-5 space-y-1">
                  {version.changes.map((change, index) => (
                    <li key={index} className="text-sm text-gray-600">
                      {change}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>

      {versions.length === 0 && (
        <div className="text-center py-6">
          <ClockIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            Nenhuma versão encontrada
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            As versões do template aparecerão aqui quando houver alterações.
          </p>
        </div>
      )}
    </div>
  );
}; 