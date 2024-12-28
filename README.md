# AI Agency Platform

Uma plataforma completa de geração de conteúdo e automação com IA, focada em fornecer soluções empresariais escaláveis e seguras.

## 🚀 Funcionalidades

- ✅ Sistema de Autenticação
- ✅ Gerenciamento de Templates
- ✅ Geração de Conteúdo com IA
- ✅ Integração com múltiplos provedores (OpenAI, Anthropic, Cohere)
- ✅ Analytics e Métricas
- ✅ Interface moderna com Chakra UI

## 🛠️ Tecnologias

### Backend
- FastAPI
- PostgreSQL
- Redis
- SQLAlchemy
- Alembic
- Python 3.12+

### Frontend
- React
- TypeScript
- Vite
- Chakra UI
- React Query
- React Router

## 📦 Instalação

### Pré-requisitos
- Python 3.12+
- Node.js 18+
- PostgreSQL
- Redis

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows

pip install -r requirements.txt
alembic upgrade head
python run.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 🔧 Configuração

1. Copie o arquivo `.env.example` para `.env` em ambos os diretórios (backend e frontend)
2. Configure as variáveis de ambiente necessárias:

### Backend (.env)
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/aiagency

# API Keys
OPENAI_API_KEY=your-api-key
ANTHROPIC_API_KEY=your-api-key
COHERE_API_KEY=your-api-key

# Security
SECRET_KEY=your-secret-key
```

### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000
VITE_ENVIRONMENT=development
```

## 🚀 Uso

1. Inicie o backend:
```bash
cd backend
source venv/bin/activate
python run.py
```

2. Inicie o frontend:
```bash
cd frontend
npm run dev
```

3. Acesse a aplicação em `http://localhost:5173`

## 📚 Documentação

- [Documentação da API](/docs/api)
- [Guia de Usuário](/docs/user_guides)
- [Arquitetura](/docs/architecture)

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👥 Autores

- Seu Nome - [@seuusername](https://github.com/seuusername)

## 🙏 Agradecimentos

- OpenAI
- Anthropic
- Cohere 