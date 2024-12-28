from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import content, templates

app = FastAPI(
    title="Content Service",
    description="Serviço de geração e gerenciamento de conteúdo",
    version="1.0.0",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas
app.include_router(content.router, prefix="/api/v1/content", tags=["content"])
app.include_router(templates.router, prefix="/api/v1/templates", tags=["templates"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "content-service"} 