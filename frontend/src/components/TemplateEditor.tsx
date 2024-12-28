import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useTemplate } from '../hooks/useTemplate';
import { Template, Variable, ValidationRule, Parameter } from '../types';
import './TemplateEditor.css';

type TabType = 'editor' | 'variables' | 'validation' | 'parameters';

export const TemplateEditor: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { template, updateTemplate, loading, error: templateError } = useTemplate(id);
  const [activeTab, setActiveTab] = useState<TabType>('editor');
  const [error, setError] = useState<string | null>(null);

  const handleBasicInfoUpdate = async (info: Partial<Template>) => {
    if (!template) return;
    
    try {
      setError(null);
      const updatedTemplate = {
        ...template,
        ...info,
        updatedAt: new Date().toISOString()
      };
      await updateTemplate(updatedTemplate);
    } catch (err) {
      console.error('Erro ao atualizar informações básicas:', err);
      setError('Erro ao salvar as alterações. Por favor, tente novamente.');
    }
  };

  const handleAddParameter = () => {
    if (!template) return;

    const newParameter: Parameter = {
      name: '',
      type: 'string',
      description: '',
      required: false
    };

    handleBasicInfoUpdate({
      parameters: [...template.parameters, newParameter]
    });
  };

  const handleParameterChange = (index: number, field: keyof Parameter, value: string | boolean) => {
    if (!template) return;

    const updatedParameters = [...template.parameters];
    updatedParameters[index] = {
      ...updatedParameters[index],
      [field]: value
    };

    handleBasicInfoUpdate({
      parameters: updatedParameters
    });
  };

  const handleRemoveParameter = (index: number) => {
    if (!template) return;

    const updatedParameters = template.parameters.filter((_, i) => i !== index);
    handleBasicInfoUpdate({
      parameters: updatedParameters
    });
  };

  const handleAddVariable = () => {
    if (!template) return;

    const newVariable: Variable = {
      name: '',
      type: 'text',
      defaultValue: '',
      required: false,
      description: ''
    };

    handleBasicInfoUpdate({
      variables: [...template.variables, newVariable]
    });
  };

  const handleVariableChange = (index: number, field: keyof Variable, value: any) => {
    if (!template) return;

    const updatedVariables = [...template.variables];
    updatedVariables[index] = {
      ...updatedVariables[index],
      [field]: value
    };

    handleBasicInfoUpdate({
      variables: updatedVariables
    });
  };

  const handleRemoveVariable = (index: number) => {
    if (!template) return;

    const updatedVariables = template.variables.filter((_, i) => i !== index);
    handleBasicInfoUpdate({
      variables: updatedVariables
    });
  };

  const handleAddValidationRule = () => {
    if (!template) return;

    const newRule: ValidationRule = {
      id: Date.now().toString(),
      field: '',
      type: 'required',
      value: '',
      message: ''
    };

    handleBasicInfoUpdate({
      validationRules: [...template.validationRules, newRule]
    });
  };

  const handleValidationRuleChange = (index: number, field: keyof ValidationRule, value: any) => {
    if (!template) return;

    const updatedRules = [...template.validationRules];
    updatedRules[index] = {
      ...updatedRules[index],
      [field]: value
    };

    handleBasicInfoUpdate({
      validationRules: updatedRules
    });
  };

  const handleRemoveValidationRule = (index: number) => {
    if (!template) return;

    const updatedRules = template.validationRules.filter((_, i) => i !== index);
    handleBasicInfoUpdate({
      validationRules: updatedRules
    });
  };

  if (loading) {
    return <div>Carregando...</div>;
  }

  if (templateError || !template) {
    return <div>Erro ao carregar template</div>;
  }

  return (
    <div className="template-editor">
      <div className="tabs">
        <button 
          className={activeTab === 'editor' ? 'active' : ''} 
          onClick={() => setActiveTab('editor')}
        >
          Editor
        </button>
        <button 
          className={activeTab === 'parameters' ? 'active' : ''} 
          onClick={() => setActiveTab('parameters')}
        >
          Parâmetros
        </button>
        <button 
          className={activeTab === 'variables' ? 'active' : ''} 
          onClick={() => setActiveTab('variables')}
        >
          Variáveis
        </button>
        <button 
          className={activeTab === 'validation' ? 'active' : ''} 
          onClick={() => setActiveTab('validation')}
        >
          Validação
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {activeTab === 'editor' && (
        <div className="basic-info">
          <div className="form-group">
            <label htmlFor="name">Nome</label>
            <input
              id="name"
              type="text"
              value={template.name}
              onChange={(e) => handleBasicInfoUpdate({ name: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label htmlFor="description">Descrição</label>
            <textarea
              id="description"
              value={template.description}
              onChange={(e) => handleBasicInfoUpdate({ description: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label htmlFor="prompt">Prompt</label>
            <textarea
              id="prompt"
              value={template.prompt}
              onChange={(e) => handleBasicInfoUpdate({ prompt: e.target.value })}
            />
          </div>
        </div>
      )}

      {activeTab === 'parameters' && (
        <div className="parameters">
          <button 
            type="button" 
            onClick={handleAddParameter}
            data-testid="add-parameter-button"
          >
            Adicionar Parâmetro
          </button>
          {template.parameters.map((parameter: Parameter, index: number) => (
            <div key={index} className="parameter-item">
              <input
                type="text"
                value={parameter.name}
                onChange={(e) => handleParameterChange(index, 'name', e.target.value)}
                placeholder="Nome do parâmetro"
              />
              <select
                value={parameter.type}
                onChange={(e) => handleParameterChange(index, 'type', e.target.value as 'string' | 'number')}
              >
                <option value="string">Texto</option>
                <option value="number">Número</option>
              </select>
              <input
                type="text"
                value={parameter.description || ''}
                onChange={(e) => handleParameterChange(index, 'description', e.target.value)}
                placeholder="Descrição"
              />
              <label>
                <input
                  type="checkbox"
                  checked={parameter.required}
                  onChange={(e) => handleParameterChange(index, 'required', e.target.checked)}
                />
                Obrigatório
              </label>
              <button className="remove" onClick={() => handleRemoveParameter(index)}>Remover</button>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'variables' && (
        <div className="variables">
          <button 
            type="button" 
            onClick={handleAddVariable}
            data-testid="add-variable-button"
          >
            Adicionar Variável
          </button>
          {template.variables.map((variable: Variable, index: number) => (
            <div key={index} className="variable-item">
              <input
                type="text"
                value={variable.name}
                onChange={(e) => handleVariableChange(index, 'name', e.target.value)}
                placeholder="Nome da variável"
              />
              <select
                value={variable.type}
                onChange={(e) => handleVariableChange(index, 'type', e.target.value)}
              >
                <option value="text">Texto</option>
                <option value="number">Número</option>
                <option value="boolean">Booleano</option>
              </select>
              <input
                type="text"
                value={variable.defaultValue}
                onChange={(e) => handleVariableChange(index, 'defaultValue', e.target.value)}
                placeholder="Valor padrão"
              />
              <input
                type="text"
                value={variable.description || ''}
                onChange={(e) => handleVariableChange(index, 'description', e.target.value)}
                placeholder="Descrição"
              />
              <label>
                <input
                  type="checkbox"
                  checked={variable.required}
                  onChange={(e) => handleVariableChange(index, 'required', e.target.checked)}
                />
                Obrigatório
              </label>
              <button className="remove" onClick={() => handleRemoveVariable(index)}>Remover</button>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'validation' && (
        <div className="validation">
          <button type="button" onClick={handleAddValidationRule}>Adicionar Regra</button>
          {template.validationRules.map((rule: ValidationRule, index: number) => (
            <div key={rule.id} className="rule-item">
              <input
                type="text"
                value={rule.field}
                onChange={(e) => handleValidationRuleChange(index, 'field', e.target.value)}
                placeholder="Campo"
              />
              <select
                value={rule.type}
                onChange={(e) => handleValidationRuleChange(index, 'type', e.target.value)}
              >
                <option value="required">Obrigatório</option>
                <option value="minLength">Comprimento mínimo</option>
                <option value="maxLength">Comprimento máximo</option>
                <option value="regex">Expressão regular</option>
                <option value="custom">Personalizado</option>
              </select>
              <input
                type="text"
                value={rule.value}
                onChange={(e) => handleValidationRuleChange(index, 'value', e.target.value)}
                placeholder="Valor"
              />
              <input
                type="text"
                value={rule.message}
                onChange={(e) => handleValidationRuleChange(index, 'message', e.target.value)}
                placeholder="Mensagem"
              />
              {rule.type === 'custom' && (
                <textarea
                  value={rule.customValidation || ''}
                  onChange={(e) => handleValidationRuleChange(index, 'customValidation', e.target.value)}
                  placeholder="Função de validação personalizada"
                />
              )}
              <button className="remove" onClick={() => handleRemoveValidationRule(index)}>Remover</button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}; 