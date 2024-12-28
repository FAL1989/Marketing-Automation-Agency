from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import content, generations
from app.core.config import settings

app = FastAPI(
    title="Content Service",
    description="Serviço de geração e gerenciamento de conteúdo",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar os domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas
app.include_router(content.router, prefix="/contents", tags=["contents"])
app.include_router(generations.router, prefix="/generations", tags=["generations"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "content"} 