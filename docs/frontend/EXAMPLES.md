# Exemplos de Implementação

## Casos de Uso Comuns

### 1. Criação de Template com Validação

```typescript
import { FC, useState } from 'react';
import { useTemplate } from '@/hooks/useTemplate';
import { useNotification } from '@/hooks/useNotification';
import { validateTemplate } from '@/utils/validation';
import { ITemplate } from '@/types';

export const TemplateCreator: FC = () => {
  const [template, setTemplate] = useState<ITemplate>({
    name: '',
    content: '',
    parameters: [],
    variables: []
  });
  
  const { save } = useTemplate();
  const { showSuccess, showError } = useNotification();
  
  const handleSubmit = async () => {
    try {
      // Validação
      const errors = validateTemplate(template);
      if (errors.length > 0) {
        showError(errors[0]);
        return;
      }
      
      // Salvar
      await save(template);
      showSuccess('Template criado com sucesso!');
      
    } catch (error) {
      showError('Erro ao criar template');
    }
  };
  
  return (
    <form onSubmit={handleSubmit}>
      {/* Implementação do formulário */}
    </form>
  );
};
```

### 2. Geração de Conteúdo com Stream

```typescript
import { FC, useState } from 'react';
import { useAI } from '@/hooks/useAI';
import { useLoading } from '@/hooks/useLoading';

export const ContentGenerator: FC<{ templateId: string }> = ({ templateId }) => {
  const [content, setContent] = useState('');
  const { streamGenerate } = useAI();
  const { setLoading } = useLoading();
  
  const handleGenerate = async () => {
    try {
      setLoading(true);
      
      // Stream de geração
      await streamGenerate(templateId, {
        onToken: (token) => {
          setContent(prev => prev + token);
        },
        onError: (error) => {
          console.error('Erro na geração:', error);
        },
        onComplete: () => {
          setLoading(false);
        }
      });
      
    } catch (error) {
      setLoading(false);
      console.error('Erro:', error);
    }
  };
  
  return (
    <div>
      <button onClick={handleGenerate}>Gerar Conteúdo</button>
      <pre>{content}</pre>
    </div>
  );
};
```

### 3. Histórico de Gerações com Paginação

```typescript
import { FC, useState } from 'react';
import { useQuery } from 'react-query';
import { fetchGenerations } from '@/services/api';
import { Pagination } from '@/components/common';

export const GenerationHistory: FC = () => {
  const [page, setPage] = useState(1);
  const pageSize = 10;
  
  const { data, isLoading } = useQuery(
    ['generations', page],
    () => fetchGenerations({ page, pageSize }),
    {
      keepPreviousData: true
    }
  );
  
  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };
  
  if (isLoading) return <Loading />;
  
  return (
    <div>
      <table>
        <thead>
          <tr>
            <th>Data</th>
            <th>Template</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {data.items.map(generation => (
            <tr key={generation.id}>
              <td>{formatDate(generation.createdAt)}</td>
              <td>{generation.templateName}</td>
              <td>{generation.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
      
      <Pagination
        currentPage={page}
        totalPages={data.totalPages}
        onPageChange={handlePageChange}
      />
    </div>
  );
};
```

### 4. Gerenciamento de Estado com Context

```typescript
import { createContext, useContext, useReducer, FC } from 'react';

// Estado
interface State {
  templates: Template[];
  selectedTemplate: Template | null;
  filters: Filters;
}

// Actions
type Action =
  | { type: 'SET_TEMPLATES'; payload: Template[] }
  | { type: 'SELECT_TEMPLATE'; payload: Template }
  | { type: 'UPDATE_FILTERS'; payload: Filters };

// Context
const TemplateContext = createContext<{
  state: State;
  dispatch: React.Dispatch<Action>;
}>({
  state: {
    templates: [],
    selectedTemplate: null,
    filters: {}
  },
  dispatch: () => null
});

// Reducer
const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case 'SET_TEMPLATES':
      return { ...state, templates: action.payload };
    case 'SELECT_TEMPLATE':
      return { ...state, selectedTemplate: action.payload };
    case 'UPDATE_FILTERS':
      return { ...state, filters: action.payload };
    default:
      return state;
  }
};

// Provider
export const TemplateProvider: FC = ({ children }) => {
  const [state, dispatch] = useReducer(reducer, {
    templates: [],
    selectedTemplate: null,
    filters: {}
  });
  
  return (
    <TemplateContext.Provider value={{ state, dispatch }}>
      {children}
    </TemplateContext.Provider>
  );
};

// Hook personalizado
export const useTemplateContext = () => {
  const context = useContext(TemplateContext);
  if (!context) {
    throw new Error('useTemplateContext deve ser usado dentro de um TemplateProvider');
  }
  return context;
};
```

### 5. Integração com WebSocket para Updates em Tempo Real

```typescript
import { FC, useEffect, useState } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { IGeneration } from '@/types';

export const RealTimeGenerations: FC = () => {
  const [generations, setGenerations] = useState<IGeneration[]>([]);
  const { connect, disconnect, subscribe } = useWebSocket();
  
  useEffect(() => {
    // Conectar ao WebSocket
    connect('wss://api.example.com/generations');
    
    // Subscrever a eventos
    const unsubscribe = subscribe('generation_completed', (data) => {
      setGenerations(prev => [data, ...prev]);
    });
    
    return () => {
      unsubscribe();
      disconnect();
    };
  }, []);
  
  return (
    <div>
      <h2>Gerações em Tempo Real</h2>
      <ul>
        {generations.map(gen => (
          <li key={gen.id}>
            {gen.templateName} - {gen.status}
          </li>
        ))}
      </ul>
    </div>
  );
};
```

### 6. Cache e Otimização com React Query

```typescript
import { QueryClient, QueryClientProvider } from 'react-query';

// Configuração do cliente
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutos
      cacheTime: 30 * 60 * 1000, // 30 minutos
      retry: 3,
      refetchOnWindowFocus: false
    }
  }
});

// Hook personalizado para templates
export const useTemplates = (filters?: Filters) => {
  return useQuery(
    ['templates', filters],
    () => fetchTemplates(filters),
    {
      // Invalidar cache quando um template é criado
      onSuccess: () => {
        queryClient.invalidateQueries('templates');
      },
      // Transformar dados antes de cachear
      select: (data) => {
        return data.map(template => ({
          ...template,
          createdAt: new Date(template.createdAt)
        }));
      }
    }
  );
};

// Mutation para criar template
export const useCreateTemplate = () => {
  return useMutation(
    (template: Template) => createTemplate(template),
    {
      // Atualizar cache após criação
      onSuccess: (newTemplate) => {
        queryClient.setQueryData<Template[]>('templates', (old) => {
          return old ? [...old, newTemplate] : [newTemplate];
        });
      }
    }
  );
};
```

## Tratamento de Erros

### 1. Error Boundary com Retry

```typescript
import { Component, FC } from 'react';

interface Props {
  onRetry: () => void;
  fallback: React.ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state = {
    hasError: false,
    error: null
  };
  
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }
  
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }
  
  handleRetry = () => {
    this.setState({ hasError: false, error: null });
    this.props.onRetry();
  };
  
  render() {
    if (this.state.hasError) {
      return (
        <div>
          <h2>Algo deu errado</h2>
          <pre>{this.state.error?.message}</pre>
          <button onClick={this.handleRetry}>Tentar Novamente</button>
          {this.props.fallback}
        </div>
      );
    }
    
    return this.props.children;
  }
}
```

### 2. Tratamento de Erros de API

```typescript
import { AxiosError } from 'axios';
import { useNotification } from '@/hooks/useNotification';

interface APIError {
  code: string;
  message: string;
}

export const useErrorHandler = () => {
  const { showError } = useNotification();
  
  const handleError = (error: unknown) => {
    if (error instanceof AxiosError) {
      const apiError = error.response?.data as APIError;
      
      switch (apiError.code) {
        case 'RATE_LIMIT_EXCEEDED':
          showError('Limite de requisições excedido. Tente novamente em alguns minutos.');
          break;
        case 'INVALID_TOKEN':
          showError('Sessão expirada. Por favor, faça login novamente.');
          // Redirecionar para login
          break;
        case 'VALIDATION_ERROR':
          showError(apiError.message);
          break;
        default:
          showError('Erro inesperado. Tente novamente mais tarde.');
      }
    } else {
      showError('Erro inesperado. Tente novamente mais tarde.');
    }
  };
  
  return { handleError };
};
```

## Otimizações de Performance

### 1. Virtualização de Lista

```typescript
import { FC } from 'react';
import { VirtualList } from '@/components/common/VirtualList';
import { IGeneration } from '@/types';

interface Props {
  generations: IGeneration[];
}

export const GenerationList: FC<Props> = ({ generations }) => {
  const renderRow = (generation: IGeneration) => (
    <div className="generation-item">
      <h3>{generation.templateName}</h3>
      <p>{generation.content}</p>
    </div>
  );
  
  return (
    <VirtualList
      items={generations}
      renderRow={renderRow}
      rowHeight={100}
      overscan={5}
      containerHeight={500}
    />
  );
};
```

### 2. Debounce em Inputs

```typescript
import { FC, useState, useCallback } from 'react';
import debounce from 'lodash/debounce';

export const SearchInput: FC<{ onSearch: (term: string) => void }> = ({ onSearch }) => {
  const [value, setValue] = useState('');
  
  const debouncedSearch = useCallback(
    debounce((term: string) => {
      onSearch(term);
    }, 300),
    []
  );
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setValue(newValue);
    debouncedSearch(newValue);
  };
  
  return (
    <input
      type="text"
      value={value}
      onChange={handleChange}
      placeholder="Pesquisar..."
    />
  );
};
``` 