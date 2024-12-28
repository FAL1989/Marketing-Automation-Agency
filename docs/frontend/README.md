# Documentação do Frontend

## Visão Geral
O frontend do AI Agency é construído em React, seguindo as melhores práticas de desenvolvimento e design de interfaces. A aplicação oferece uma interface intuitiva para gerenciamento de templates, geração de conteúdo e monitoramento de métricas.

## Tecnologias Principais
- React 18
- TypeScript 5
- Material-UI v5
- React Query
- React Router v6
- Redux Toolkit
- Jest + React Testing Library
- Cypress

## Estrutura do Projeto
```
frontend/
├── src/
│   ├── components/       # Componentes reutilizáveis
│   ├── hooks/           # Custom hooks
│   ├── pages/           # Páginas/rotas da aplicação
│   ├── services/        # Serviços e integrações
│   ├── store/           # Estado global (Redux)
│   ├── styles/          # Estilos e temas
│   ├── types/           # Definições de tipos
│   └── utils/           # Funções utilitárias
├── public/              # Assets estáticos
└── tests/               # Testes E2E
```

## Componentes Principais

### 1. TemplateEditor
Componente para criação e edição de templates.

**Props:**
```typescript
interface TemplateEditorProps {
  template?: Template;
  onSave: (template: Template) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}
```

**Exemplo de Uso:**
```tsx
import { TemplateEditor } from '@/components/TemplateEditor';

function MyComponent() {
  const handleSave = async (template: Template) => {
    await saveTemplate(template);
  };

  return (
    <TemplateEditor
      onSave={handleSave}
      onCancel={() => navigate(-1)}
    />
  );
}
```

### 2. ContentGenerator
Componente para geração de conteúdo a partir de templates.

**Props:**
```typescript
interface ContentGeneratorProps {
  templateId: string;
  onGenerate: (params: GenerationParams) => Promise<string>;
  onComplete?: (result: string) => void;
}
```

**Exemplo de Uso:**
```tsx
import { ContentGenerator } from '@/components/ContentGenerator';

function MyComponent() {
  const handleGenerate = async (params) => {
    const result = await generateContent(params);
    return result;
  };

  return (
    <ContentGenerator
      templateId="template_123"
      onGenerate={handleGenerate}
      onComplete={console.log}
    />
  );
}
```

### 3. GenerationHistory
Componente para visualização do histórico de gerações.

**Props:**
```typescript
interface GenerationHistoryProps {
  userId?: string;
  templateId?: string;
  limit?: number;
  onItemClick?: (generation: Generation) => void;
}
```

**Exemplo de Uso:**
```tsx
import { GenerationHistory } from '@/components/GenerationHistory';

function MyComponent() {
  return (
    <GenerationHistory
      limit={10}
      onItemClick={(generation) => {
        setSelectedGeneration(generation);
      }}
    />
  );
}
```

### 4. MetricsDashboard
Componente para visualização de métricas e analytics.

**Props:**
```typescript
interface MetricsDashboardProps {
  timeRange: 'day' | 'week' | 'month';
  metrics: string[];
  refreshInterval?: number;
}
```

**Exemplo de Uso:**
```tsx
import { MetricsDashboard } from '@/components/MetricsDashboard';

function MyComponent() {
  return (
    <MetricsDashboard
      timeRange="week"
      metrics={['generations', 'tokens', 'costs']}
      refreshInterval={30000}
    />
  );
}
```

## Hooks Personalizados

### 1. useAI
Hook para interação com serviços de IA.

```typescript
const useAI = () => {
  const generate = async (prompt: string, options?: AIOptions) => {
    // Implementação
  };

  const streamGenerate = async (prompt: string, options?: AIOptions) => {
    // Implementação
  };

  return { generate, streamGenerate };
};
```

### 2. useTemplate
Hook para gerenciamento de templates.

```typescript
const useTemplate = (templateId?: string) => {
  const { data: template, isLoading } = useQuery(['template', templateId], () => 
    fetchTemplate(templateId)
  );

  const save = async (template: Template) => {
    // Implementação
  };

  return { template, isLoading, save };
};
```

## Serviços

### 1. API Service
Serviço para comunicação com o backend.

```typescript
class APIService {
  static async get<T>(endpoint: string, params?: object): Promise<T> {
    // Implementação
  }

  static async post<T>(endpoint: string, data: object): Promise<T> {
    // Implementação
  }
}
```

### 2. Auth Service
Serviço para gerenciamento de autenticação.

```typescript
class AuthService {
  static async login(email: string, password: string): Promise<void> {
    // Implementação
  }

  static async logout(): Promise<void> {
    // Implementação
  }
}
```

## Guias de Desenvolvimento

### 1. Padrões de Código

#### Nomenclatura
- **Componentes**: PascalCase (ex: `TemplateEditor.tsx`)
- **Hooks**: camelCase prefixado com "use" (ex: `useTemplate.ts`)
- **Utilitários**: camelCase (ex: `formatDate.ts`)
- **Constantes**: SCREAMING_SNAKE_CASE (ex: `MAX_RETRIES`)
- **Interfaces/Types**: PascalCase prefixado com "I" para interfaces (ex: `ITemplateProps`)
- **Enums**: PascalCase (ex: `TemplateStatus`)

#### Estrutura de Arquivos
```
components/
└── MyComponent/
    ├── index.tsx           # Componente principal
    ├── styles.ts           # Estilos (styled-components)
    ├── types.ts            # Tipos e interfaces
    ├── constants.ts        # Constantes específicas
    ├── utils.ts            # Funções utilitárias
    └── MyComponent.test.tsx # Testes
```

#### Imports
```typescript
// 1. React e bibliotecas externas
import { FC, useState, useEffect } from 'react';
import { useQuery } from 'react-query';

// 2. Componentes internos
import { Button } from '@/components/common';

// 3. Hooks e utilitários
import { useTemplate } from '@/hooks';
import { formatDate } from '@/utils';

// 4. Tipos e constantes
import { ITemplateProps } from './types';
import { TEMPLATE_STATUS } from './constants';

// 5. Estilos
import * as S from './styles';
```

### 2. Convenções de Desenvolvimento

#### Componentes
```typescript
// Componente Funcional com TypeScript
import { FC } from 'react';
import { IMyComponentProps } from './types';

export const MyComponent: FC<IMyComponentProps> = ({ prop1, prop2 }) => {
  // 1. Hooks
  const [state, setState] = useState<string>('');
  
  // 2. Handlers
  const handleClick = () => {
    // Implementação
  };
  
  // 3. Effects
  useEffect(() => {
    // Side effects
  }, []);
  
  // 4. Render helpers
  const renderContent = () => {
    return <div>Content</div>;
  };
  
  // 5. JSX principal
  return (
    <S.Container>
      {renderContent()}
    </S.Container>
  );
};
```

#### Hooks Personalizados
```typescript
// Hook com TypeScript
export const useMyHook = (param: string) => {
  // 1. State
  const [data, setData] = useState<Data | null>(null);
  
  // 2. Queries/Mutations
  const { data: queryData } = useQuery(['key', param], fetchData);
  
  // 3. Handlers
  const handleData = () => {
    // Implementação
  };
  
  // 4. Effects
  useEffect(() => {
    // Side effects
  }, [param]);
  
  // 5. Return
  return {
    data,
    handleData
  };
};
```

### 3. Fluxo de Trabalho

#### Desenvolvimento de Novas Features
1. **Planejamento**
   - Revisar requisitos
   - Definir interfaces e tipos
   - Planejar estrutura de componentes

2. **Implementação**
   - Criar estrutura de arquivos
   - Implementar lógica base
   - Adicionar estilos
   - Implementar testes

3. **Revisão**
   - Executar testes
   - Verificar cobertura
   - Validar acessibilidade
   - Revisar performance

#### Integração com Backend
1. **Preparação**
   - Definir contratos de API
   - Criar tipos/interfaces
   - Implementar serviços base

2. **Implementação**
   - Criar hooks de integração
   - Implementar cache (React Query)
   - Adicionar tratamento de erros
   - Implementar loading states

3. **Validação**
   - Testar diferentes cenários
   - Validar edge cases
   - Verificar tratamento de erros
   - Testar offline behavior

### 4. Tratamento de Erros

#### Hierarquia de Error Boundaries
```typescript
// Error Boundary Global
export const GlobalErrorBoundary: FC = ({ children }) => {
  return (
    <ErrorBoundary
      fallback={<GlobalErrorFallback />}
      onError={logError}
    >
      {children}
    </ErrorBoundary>
  );
};

// Error Boundary de Feature
export const FeatureErrorBoundary: FC = ({ children }) => {
  return (
    <ErrorBoundary
      fallback={<FeatureErrorFallback />}
      onError={logFeatureError}
    >
      {children}
    </ErrorBoundary>
  );
};
```

#### Tratamento de Erros de API
```typescript
// Hook de API com tratamento de erro
export const useAPI = () => {
  const handleError = (error: Error) => {
    if (error instanceof NetworkError) {
      showNetworkError();
    } else if (error instanceof ValidationError) {
      showValidationError();
    } else {
      showGenericError();
    }
  };

  return {
    handleError
  };
};
```

### 5. Performance

#### Otimizações de Renderização
```typescript
// Memo para componentes puros
export const PureComponent = memo(({ data }) => {
  return <div>{data}</div>;
}, arePropsEqual);

// Callbacks memorizados
const memoizedCallback = useCallback(() => {
  doSomething(a, b);
}, [a, b]);

// Valores computados memorizados
const memoizedValue = useMemo(() => {
  return computeExpensiveValue(a, b);
}, [a, b]);
```

#### Code Splitting
```typescript
// Lazy loading de componentes
const HeavyComponent = lazy(() => import('./HeavyComponent'));

// Suspense boundary
<Suspense fallback={<Loading />}>
  <HeavyComponent />
</Suspense>
```

## Boas Práticas

### 1. Performance
- Usar React.memo para componentes puros
- Implementar virtualização para listas longas
- Lazy loading de rotas e componentes grandes
- Otimizar re-renders com useMemo e useCallback

### 2. Acessibilidade
- Seguir WAI-ARIA guidelines
- Implementar navegação por teclado
- Manter contraste adequado
- Fornecer textos alternativos para imagens

### 3. Segurança
- Sanitizar inputs do usuário
- Evitar XSS com escape adequado
- Não expor informações sensíveis no frontend
- Validar dados antes do envio ao backend

## Troubleshooting

### Problemas Comuns

1. **Erro de Build**
```
Causa: Dependências incompatíveis
Solução: Verificar versões no package.json
```

2. **Performance Lenta**
```
Causa: Re-renders desnecessários
Solução: Usar React DevTools para identificar e corrigir
```

3. **Erro de Tipo**
```
Causa: Tipos incompatíveis
Solução: Verificar definições em types.ts
```

## Deploy

### 1. Ambiente de Desenvolvimento
```bash
# Instalar dependências
npm install

# Rodar em desenvolvimento
npm run dev

# Rodar testes
npm run test
```

### 2. Ambiente de Produção
```bash
# Build de produção
npm run build

# Preview do build
npm run preview
```

## Monitoramento

### 1. Métricas Coletadas
- Tempo de carregamento
- Taxa de erro de JavaScript
- Uso de memória
- Performance de renderização

### 2. Ferramentas
- Google Analytics
- Sentry
- Lighthouse
- React DevTools 