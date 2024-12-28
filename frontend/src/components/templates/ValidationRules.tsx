import React, { useState } from 'react';
import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline';

interface ValidationRule {
  id: string;
  field: string;
  type: 'required' | 'minLength' | 'maxLength' | 'regex' | 'custom';
  value: string | number;
  message: string;
  customValidation?: string;
}

interface ValidationRulesProps {
  rules: ValidationRule[];
  variables: Array<{ name: string; type: string }>;
  onUpdate: (rules: ValidationRule[]) => void;
}

export const ValidationRules: React.FC<ValidationRulesProps> = ({
  rules,
  variables,
  onUpdate
}) => {
  const [selectedField, setSelectedField] = useState<string>('');
  const [selectedType, setSelectedType] = useState<ValidationRule['type']>('required');

  const generateRuleId = () => `rule_${Date.now()}`;

  const handleAddRule = () => {
    if (!selectedField) return;

    const newRule: ValidationRule = {
      id: generateRuleId(),
      field: selectedField,
      type: selectedType,
      value: selectedType === 'required' ? 'true' : '',
      message: `Campo ${selectedField} é inválido`,
    };

    onUpdate([...rules, newRule]);
    setSelectedField('');
  };

  const handleRemoveRule = (ruleId: string) => {
    onUpdate(rules.filter(rule => rule.id !== ruleId));
  };

  const handleRuleChange = (ruleId: string, field: keyof ValidationRule, value: any) => {
    onUpdate(
      rules.map(rule =>
        rule.id === ruleId
          ? { ...rule, [field]: value }
          : rule
      )
    );
  };

  const getRuleValueInput = (rule: ValidationRule) => {
    switch (rule.type) {
      case 'required':
        return (
          <select
            value={rule.value.toString()}
            onChange={(e) => handleRuleChange(rule.id, 'value', e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          >
            <option value="true">Sim</option>
            <option value="false">Não</option>
          </select>
        );
      case 'minLength':
      case 'maxLength':
        return (
          <input
            type="number"
            value={rule.value}
            onChange={(e) => handleRuleChange(rule.id, 'value', parseInt(e.target.value))}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            min="0"
          />
        );
      case 'regex':
        return (
          <input
            type="text"
            value={rule.value}
            onChange={(e) => handleRuleChange(rule.id, 'value', e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            placeholder="Expressão regular"
          />
        );
      case 'custom':
        return (
          <textarea
            value={rule.customValidation || ''}
            onChange={(e) => handleRuleChange(rule.id, 'customValidation', e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            rows={3}
            placeholder="function validate(value) { return value > 0; }"
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white shadow-sm rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Adicionar Nova Regra</h3>
        
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Campo</label>
            <select
              value={selectedField}
              onChange={(e) => setSelectedField(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            >
              <option value="">Selecione um campo</option>
              {variables.map(variable => (
                <option key={variable.name} value={variable.name}>
                  {variable.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Tipo de Validação</label>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value as ValidationRule['type'])}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            >
              <option value="required">Obrigatório</option>
              <option value="minLength">Comprimento Mínimo</option>
              <option value="maxLength">Comprimento Máximo</option>
              <option value="regex">Expressão Regular</option>
              <option value="custom">Personalizada</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              type="button"
              onClick={handleAddRule}
              disabled={!selectedField}
              className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <PlusIcon className="h-5 w-5 mr-2" />
              Adicionar Regra
            </button>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {rules.map(rule => (
          <div key={rule.id} className="bg-gray-50 rounded-lg p-4 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Campo</label>
                <select
                  value={rule.field}
                  onChange={(e) => handleRuleChange(rule.id, 'field', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                >
                  {variables.map(variable => (
                    <option key={variable.name} value={variable.name}>
                      {variable.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Tipo</label>
                <select
                  value={rule.type}
                  onChange={(e) => handleRuleChange(rule.id, 'type', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                >
                  <option value="required">Obrigatório</option>
                  <option value="minLength">Comprimento Mínimo</option>
                  <option value="maxLength">Comprimento Máximo</option>
                  <option value="regex">Expressão Regular</option>
                  <option value="custom">Personalizada</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  {rule.type === 'custom' ? 'Validação Personalizada' : 'Valor'}
                </label>
                {getRuleValueInput(rule)}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Mensagem de Erro</label>
                <input
                  type="text"
                  value={rule.message}
                  onChange={(e) => handleRuleChange(rule.id, 'message', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>
            </div>

            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => handleRemoveRule(rule.id)}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-red-700 bg-red-100 hover:bg-red-200"
              >
                <TrashIcon className="h-5 w-5 mr-2" />
                Remover Regra
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}; 