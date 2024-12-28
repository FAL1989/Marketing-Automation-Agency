# Guia de Contribuição

## Introdução
Obrigado por considerar contribuir para nosso projeto! Este documento fornece as diretrizes e melhores práticas para contribuir com o desenvolvimento.

## Índice
1. [Ambiente de Desenvolvimento](#ambiente-de-desenvolvimento)
2. [Padrões de Código](#padrões-de-código)
3. [Fluxo de Trabalho](#fluxo-de-trabalho)
4. [Testes](#testes)
5. [Documentação](#documentação)

## Ambiente de Desenvolvimento

### Requisitos
- Node.js 18+
- TypeScript 5+
- Docker
- Git

### Setup
1. Clone o repositório:
```bash
git clone https://github.com/empresa/projeto.git
cd projeto
```

2. Instale as dependências:
```bash
# Frontend
cd frontend
npm install

# Backend
cd ../backend
npm install
```

3. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite .env com suas configurações
```

4. Inicie os serviços:
```bash
docker-compose up -d
npm run dev
```

## Padrões de Código

### Estilo
- Utilizamos ESLint e Prettier
- Commits seguem Conventional Commits
- TypeScript strict mode habilitado

### Estrutura de Arquivos
```
src/
  ├── components/     # Componentes React
  ├── hooks/         # Custom hooks
  ├── pages/         # Páginas/rotas
  ├── services/      # Serviços/API
  ├── types/         # Tipos TypeScript
  └── utils/         # Utilitários
```

### Nomenclatura
- Componentes: PascalCase
- Funções/hooks: camelCase
- Arquivos de teste: `.test.ts(x)`
- Tipos/interfaces: PascalCase

## Fluxo de Trabalho

### Branches
- `main`: Produção
- `develop`: Desenvolvimento
- `feature/*`: Novas funcionalidades
- `fix/*`: Correções
- `docs/*`: Documentação

### Processo
1. Crie uma branch a partir de `develop`
2. Desenvolva a funcionalidade/correção
3. Escreva/atualize testes
4. Atualize a documentação
5. Crie um Pull Request
6. Aguarde review

### Pull Requests
- Use o template fornecido
- Inclua descrição clara
- Referencie issues relacionadas
- Aguarde CI/CD passar
- Obtenha aprovação de reviewer

## Testes

### Tipos de Teste
- Unitários: Jest + Testing Library
- Integração: Supertest
- E2E: Cypress

### Executando Testes
```bash
# Unitários
npm run test

# Cobertura
npm run test:coverage

# E2E
npm run test:e2e
```

### Diretrizes
- Mantenha cobertura > 85%
- Teste casos de erro
- Use mocks apropriadamente
- Evite testes frágeis

## Documentação

### Código
- JSDoc para funções/componentes
- Comentários para lógica complexa
- README em cada diretório principal

### API
- OpenAPI/Swagger
- Exemplos de uso
- Códigos de erro
- Rate limits

### Commits
```
feat: adiciona novo componente
^--^  ^--------------------^
|     |
|     +-> Descrição clara e concisa
|
+-------> Tipo: feat, fix, docs, style, refactor, test, chore
```

## Monitoramento e Métricas

### Grafana
- Dashboards personalizados
- Métricas de performance
- Alertas configuráveis

### Logs
- Estruturados em JSON
- Níveis apropriados
- Contexto suficiente

## Segurança

### Boas Práticas
- Evite credenciais no código
- Valide inputs
- Use HTTPS
- Implemente rate limiting

### Vulnerabilidades
- Reporte privadamente
- Use issues security
- Atualize dependências 