import React, { useState } from 'react';
import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline';

interface Variable {
  name: string;
  type: 'text' | 'number' | 'boolean' | 'select';
  defaultValue: any;
  required: boolean;
  options?: string[]; // Para tipo 'select'
  description?: string;
}

interface VariableEditorProps {
  variables: Variable[];
  onChange: (variables: Variable[]) => void;
  onValidate?: (variables: Variable[]) => { isValid: boolean; errors: string[] };
}

export const VariableEditor: React.FC<VariableEditorProps> = ({
  variables,
  onChange,
  onValidate
}) => {
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  const handleAddVariable = () => {
    const newVariable: Variable = {
      name: `variavel_${variables.length + 1}`,
      type: 'text',
      defaultValue: '',
      required: false
    };
    onChange([...variables, newVariable]);
  };

  const handleRemoveVariable = (index: number) => {
    const newVariables = variables.filter((_, i) => i !== index);
    onChange(newVariables);
  };

  const handleVariableChange = (index: number, field: keyof Variable, value: any) => {
    const newVariables = variables.map((variable, i) => {
      if (i === index) {
        // Resetar defaultValue se o tipo mudar
        if (field === 'type') {
          return {
            ...variable,
            [field]: value,
            defaultValue: value === 'boolean' ? false : value === 'number' ? 0 : ''
          };
        }
        return { ...variable, [field]: value };
      }
      return variable;
    });
    
    onChange(newVariables);
    
    if (onValidate) {
      const result = onValidate(newVariables);
      setValidationErrors(result.errors);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium text-gray-900">Variáveis do Template</h3>
        <button
          type="button"
          onClick={handleAddVariable}
          className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          Adicionar Variável
        </button>
      </div>

      {validationErrors.length > 0 && (
        <div className="rounded-md bg-red-50 p-4">
          <ul className="list-disc pl-5 space-y-1">
            {validationErrors.map((error, index) => (
              <li key={index} className="text-sm text-red-700">{error}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="space-y-4">
        {variables.map((variable, index) => (
          <div key={index} className="bg-gray-50 p-4 rounded-lg space-y-3">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Nome</label>
                <input
                  type="text"
                  value={variable.name}
                  onChange={(e) => handleVariableChange(index, 'name', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Tipo</label>
                <select
                  value={variable.type}
                  onChange={(e) => handleVariableChange(index, 'type', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                >
                  <option value="text">Texto</option>
                  <option value="number">Número</option>
                  <option value="boolean">Booleano</option>
                  <option value="select">Seleção</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Valor Padrão</label>
                {variable.type === 'boolean' ? (
                  <select
                    value={variable.defaultValue.toString()}
                    onChange={(e) => handleVariableChange(index, 'defaultValue', e.target.value === 'true')}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  >
                    <option value="true">Verdadeiro</option>
                    <option value="false">Falso</option>
                  </select>
                ) : (
                  <input
                    type={variable.type === 'number' ? 'number' : 'text'}
                    value={variable.defaultValue}
                    onChange={(e) => handleVariableChange(index, 'defaultValue', variable.type === 'number' ? Number(e.target.value) : e.target.value)}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  />
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Descrição</label>
                <input
                  type="text"
                  value={variable.description || ''}
                  onChange={(e) => handleVariableChange(index, 'description', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  placeholder="Descrição opcional"
                />
              </div>
            </div>

            {variable.type === 'select' && (
              <div>
                <label className="block text-sm font-medium text-gray-700">Opções (separadas por vírgula)</label>
                <input
                  type="text"
                  value={variable.options?.join(', ') || ''}
                  onChange={(e) => handleVariableChange(index, 'options', e.target.value.split(',').map(opt => opt.trim()))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  placeholder="Opção 1, Opção 2, Opção 3"
                />
              </div>
            )}

            <div className="flex items-center space-x-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={variable.required}
                  onChange={(e) => handleVariableChange(index, 'required', e.target.checked)}
                  className="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
                <span className="ml-2 text-sm text-gray-600">Obrigatório</span>
              </label>
              
              <button
                type="button"
                onClick={() => handleRemoveVariable(index)}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-red-700 bg-red-100 hover:bg-red-200"
              >
                <TrashIcon className="h-5 w-5 mr-2" />
                Remover
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}; 