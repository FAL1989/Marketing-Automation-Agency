# Guia de Testes do Frontend

## Visão Geral
Este guia estabelece as práticas e padrões para testes no frontend da aplicação AI Agency.

## Tipos de Testes

### 1. Testes Unitários

#### Configuração
```typescript
// jest.config.js
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1'
  }
};
```

#### Estrutura de Testes
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { MyComponent } from './MyComponent';

describe('MyComponent', () => {
  beforeEach(() => {
    // Setup comum
  });

  it('should render correctly', () => {
    render(<MyComponent />);
    expect(screen.getByTestId('my-component')).toBeInTheDocument();
  });

  it('should handle user interactions', () => {
    render(<MyComponent />);
    const button = screen.getByRole('button');
    fireEvent.click(button);
    expect(screen.getByText('Clicked')).toBeInTheDocument();
  });

  it('should handle async operations', async () => {
    render(<MyComponent />);
    const button = screen.getByRole('button');
    fireEvent.click(button);
    expect(await screen.findByText('Loaded')).toBeInTheDocument();
  });
});
```

#### Mocks
```typescript
// Mock de serviço
jest.mock('@/services/api', () => ({
  fetchData: jest.fn().mockResolvedValue({ data: 'test' })
}));

// Mock de hook
jest.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    isAuthenticated: true,
    user: { id: '1', name: 'Test User' }
  })
}));
```

### 2. Testes de Integração

#### Setup com React Testing Library
```typescript
import { render } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ThemeProvider } from 'styled-components';
import { theme } from '@/styles/theme';

const AllTheProviders = ({ children }) => {
  const queryClient = new QueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        {children}
      </ThemeProvider>
    </QueryClientProvider>
  );
};

const customRender = (ui, options) =>
  render(ui, { wrapper: AllTheProviders, ...options });

export * from '@testing-library/react';
export { customRender as render };
```

#### Exemplo de Teste de Integração
```typescript
import { render, screen, waitFor } from '@/tests/utils';
import { TemplateEditor } from './TemplateEditor';

describe('TemplateEditor Integration', () => {
  it('should create template and show success message', async () => {
    render(<TemplateEditor />);
    
    // Preencher formulário
    fireEvent.change(screen.getByLabelText('Nome'), {
      target: { value: 'Meu Template' }
    });
    
    // Submeter
    fireEvent.click(screen.getByText('Salvar'));
    
    // Verificar resultado
    await waitFor(() => {
      expect(screen.getByText('Template criado com sucesso')).toBeInTheDocument();
    });
  });
});
```

### 3. Testes E2E com Cypress

#### Configuração
```typescript
// cypress.config.ts
import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    supportFile: 'cypress/support/e2e.ts'
  }
});
```

#### Comandos Personalizados
```typescript
// cypress/support/commands.ts
Cypress.Commands.add('login', (email: string, password: string) => {
  cy.visit('/login');
  cy.get('[data-testid=email]').type(email);
  cy.get('[data-testid=password]').type(password);
  cy.get('[data-testid=submit]').click();
});

Cypress.Commands.add('createTemplate', (name: string) => {
  cy.get('[data-testid=new-template]').click();
  cy.get('[data-testid=template-name]').type(name);
  cy.get('[data-testid=save-template]').click();
});
```

#### Exemplo de Teste E2E
```typescript
describe('Template Creation Flow', () => {
  beforeEach(() => {
    cy.login('user@example.com', 'password');
  });

  it('should create and generate content from template', () => {
    // Criar template
    cy.createTemplate('E-commerce Product Description');
    
    // Configurar parâmetros
    cy.get('[data-testid=add-parameter]').click();
    cy.get('[data-testid=parameter-name]').type('productName');
    
    // Gerar conteúdo
    cy.get('[data-testid=generate]').click();
    cy.get('[data-testid=result]').should('be.visible');
  });
});
```

## Boas Práticas

### 1. Organização de Testes
- Um arquivo de teste por componente/hook
- Agrupar testes relacionados em describe blocks
- Usar nomes descritivos para os testes
- Manter testes independentes entre si

### 2. Seletores
Prioridade de seletores (do mais recomendado ao menos recomendado):
1. Roles e Labels (getByRole, getByLabelText)
2. Text content (getByText)
3. Test IDs (getByTestId)
4. DOM structure (querySelector)

### 3. Asserções
- Testar comportamento, não implementação
- Verificar estados visuais e de dados
- Usar matchers apropriados
- Evitar asserções frágeis

### 4. Mocks e Stubs
- Mockar apenas o necessário
- Usar dados realistas
- Documentar mocks complexos
- Limpar mocks após cada teste

## Troubleshooting

### Problemas Comuns

1. **Testes Assíncronos Falhando**
```typescript
// ❌ Errado
it('should load data', () => {
  render(<MyComponent />);
  expect(screen.getByText('Loaded')).toBeInTheDocument();
});

// ✅ Correto
it('should load data', async () => {
  render(<MyComponent />);
  expect(await screen.findByText('Loaded')).toBeInTheDocument();
});
```

2. **Testes Quebrando por Mudanças de Estado**
```typescript
// ❌ Errado
it('should update count', () => {
  const { result } = renderHook(() => useState(0));
  act(() => {
    result.current[1](1);
  });
  expect(result.current[0]).toBe(1);
});

// ✅ Correto
it('should update count', () => {
  const { result } = renderHook(() => useState(0));
  act(() => {
    result.current[1](1);
  });
  expect(result.current[0]).toBe(1);
  cleanup();
});
```

## Scripts de Teste

### Package.json
```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:e2e": "cypress run",
    "test:e2e:open": "cypress open"
  }
}
``` 