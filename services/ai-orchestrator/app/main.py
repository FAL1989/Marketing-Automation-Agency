from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
from app.api.routes import generate
from shared.messaging import message_broker

app = FastAPI(
    title="AI Orchestrator Service",
    description="Serviço de orquestração de provedores de IA",
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

# Adicionar endpoint de métricas do Prometheus
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Incluir rotas
app.include_router(generate.router, prefix="/api/v1", tags=["generate"])

@app.on_event("startup")
async def startup_event():
    """
    Inicializa conexões e configurações necessárias
    """
    # Conectar ao RabbitMQ
    await message_broker.connect()

@app.on_event("shutdown")
async def shutdown_event():
    """
    Fecha conexões ao encerrar a aplicação
    """
    await message_broker.close()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-orchestrator"} 