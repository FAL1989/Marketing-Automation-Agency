import React, { useState, useEffect } from 'react';
import { Template, TemplateParameter } from '../types';
import { XMarkIcon, PlusIcon, TrashIcon } from '@heroicons/react/24/solid';

export interface TemplateFormProps {
  template?: Template | null;
  onSubmit: (template: Omit<Template, 'id' | 'createdAt' | 'updatedAt'>) => Promise<void>;
  onCancel: () => void;
}

interface ParameterInput {
  name: string;
  label?: string;
  type: 'text' | 'number' | 'select';
  description?: string;
  required: boolean;
  placeholder?: string;
  options?: string[];
}

export const TemplateForm: React.FC<TemplateFormProps> = ({
  template,
  onSubmit,
  onCancel
}) => {
  const [formData, setFormData] = useState<Partial<Template>>({
    name: '',
    description: '',
    content: '',
    parameters: [],
    isPublic: false,
    isActive: true
  });

  const [newParameter, setNewParameter] = useState<ParameterInput>({
    name: '',
    description: '',
    type: 'text',
    required: false,
    label: '',
    placeholder: '',
    options: []
  });

  useEffect(() => {
    if (template) {
      setFormData({
        ...template
      });
    }
  }, [template]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    }));
  };

  const handleParameterChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setNewParameter(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    }));
  };

  const handleOptionsChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const options = e.target.value.split('\n').filter(option => option.trim() !== '');
    setNewParameter(prev => ({
      ...prev,
      options
    }));
  };

  const addParameter = () => {
    if (newParameter.name.trim()) {
      setFormData(prev => ({
        ...prev,
        parameters: [...(prev.parameters || []), newParameter as TemplateParameter]
      }));
      setNewParameter({
        name: '',
        description: '',
        type: 'text',
        required: false,
        label: '',
        placeholder: '',
        options: []
      });
    }
  };

  const removeParameter = (index: number) => {
    setFormData(prev => ({
      ...prev,
      parameters: prev.parameters?.filter((_, i) => i !== index) || []
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await onSubmit({
        name: formData.name || '',
        description: formData.description || '',
        content: formData.content || '',
        parameters: formData.parameters || [],
        isPublic: formData.isPublic || false,
        isActive: formData.isActive || true
      });
      setFormData({
        name: '',
        description: '',
        content: '',
        parameters: [],
        isPublic: false,
        isActive: true
      });
    } catch (err) {
      console.error('Erro ao salvar template:', err);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-medium text-gray-900">
          {template ? 'Editar Template' : 'Novo Template'}
        </h3>
        <button
          onClick={onCancel}
          className="text-gray-400 hover:text-gray-500"
        >
          <XMarkIcon className="h-6 w-6" />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700">
            Nome
          </label>
          <input
            type="text"
            name="name"
            id="name"
            value={formData.name}
            onChange={handleChange}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            required
          />
        </div>

        <div>
          <label htmlFor="description" className="block text-sm font-medium text-gray-700">
            Descrição
          </label>
          <textarea
            name="description"
            id="description"
            value={formData.description}
            onChange={handleChange}
            rows={3}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          />
        </div>

        <div>
          <label htmlFor="content" className="block text-sm font-medium text-gray-700">
            Conteúdo do Template
          </label>
          <textarea
            name="content"
            id="content"
            value={formData.content}
            onChange={handleChange}
            rows={8}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm font-mono"
            required
            placeholder="Digite o conteúdo do template aqui..."
          />
        </div>

        <div>
          <div className="flex justify-between items-center mb-4">
            <label className="block text-sm font-medium text-gray-700">
              Parâmetros
            </label>
          </div>

          <div className="space-y-4">
            {formData.parameters?.map((param, index) => (
              <div key={index} className="flex items-center gap-4 p-4 bg-gray-50 rounded-md">
                <div className="flex-1">
                  <p className="font-medium">{param.name}</p>
                  <p className="text-sm text-gray-500">{param.description}</p>
                  <div className="flex gap-4 mt-1 text-sm text-gray-500">
                    <span>Tipo: {param.type}</span>
                    <span>{param.required ? 'Obrigatório' : 'Opcional'}</span>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => removeParameter(index)}
                  className="text-red-500 hover:text-red-700"
                >
                  <TrashIcon className="h-5 w-5" />
                </button>
              </div>
            ))}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <input
                  type="text"
                  name="name"
                  value={newParameter.name}
                  onChange={handleParameterChange}
                  placeholder="Nome do parâmetro"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>
              <div>
                <input
                  type="text"
                  name="label"
                  value={newParameter.label}
                  onChange={handleParameterChange}
                  placeholder="Rótulo do parâmetro"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>
              <div>
                <input
                  type="text"
                  name="description"
                  value={newParameter.description}
                  onChange={handleParameterChange}
                  placeholder="Descrição do parâmetro"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>
              <div>
                <input
                  type="text"
                  name="placeholder"
                  value={newParameter.placeholder}
                  onChange={handleParameterChange}
                  placeholder="Texto de exemplo"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>
              <div>
                <select
                  name="type"
                  value={newParameter.type}
                  onChange={handleParameterChange}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                >
                  <option value="text">Texto</option>
                  <option value="number">Número</option>
                  <option value="select">Seleção</option>
                </select>
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  name="required"
                  id="required"
                  checked={newParameter.required}
                  onChange={handleParameterChange}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label htmlFor="required" className="ml-2 block text-sm text-gray-900">
                  Obrigatório
                </label>
              </div>
              {newParameter.type === 'select' && (
                <div className="col-span-2">
                  <label htmlFor="options" className="block text-sm font-medium text-gray-700">
                    Opções (uma por linha)
                  </label>
                  <textarea
                    name="options"
                    id="options"
                    value={newParameter.options?.join('\n')}
                    onChange={handleOptionsChange}
                    rows={3}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="Digite as opções, uma por linha"
                  />
                </div>
              )}
              <div className="col-span-2">
                <button
                  type="button"
                  onClick={addParameter}
                  className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  <PlusIcon className="h-5 w-5 mr-2" />
                  Adicionar Parâmetro
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            name="isPublic"
            id="isPublic"
            checked={formData.isPublic}
            onChange={handleChange}
            className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
          />
          <label htmlFor="isPublic" className="ml-2 block text-sm text-gray-900">
            Tornar template público
          </label>
        </div>

        <div className="flex justify-end gap-x-3 pt-4">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Cancelar
          </button>
          <button
            type="submit"
            className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Salvar
          </button>
        </div>
      </form>
    </div>
  );
}; 