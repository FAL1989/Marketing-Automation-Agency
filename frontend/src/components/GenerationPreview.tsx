import React from 'react';
import { CheckIcon, PencilIcon } from '@heroicons/react/24/outline';

interface GenerationPreviewProps {
    content: string;
    onApprove: () => void;
    onEdit: () => void;
}

export const GenerationPreview: React.FC<GenerationPreviewProps> = ({
    content,
    onApprove,
    onEdit
}) => {
    return (
        <div className="mt-4 bg-gray-50 rounded-lg p-4">
            <h3 className="text-lg font-medium text-gray-900 mb-2">
                Prévia do Conteúdo
            </h3>
            
            <div className="prose max-w-none mb-4">
                {content}
            </div>
            
            <div className="flex justify-end space-x-4">
                <button
                    onClick={onEdit}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                    <PencilIcon className="h-4 w-4 mr-2" />
                    Editar
                </button>
                
                <button
                    onClick={onApprove}
                    className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                >
                    <CheckIcon className="h-4 w-4 mr-2" />
                    Aprovar
                </button>
            </div>
        </div>
    );
}; 