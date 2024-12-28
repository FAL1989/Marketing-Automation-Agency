from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
from app.api.routes import metrics
from app.services.event_processor import event_processor
from app.core.clickhouse import clickhouse_client
from shared.cache import cache_manager

app = FastAPI(
    title="Analytics Service",
    description="Serviço de analytics e métricas",
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
app.include_router(metrics.router, prefix="/api/v1", tags=["metrics"])

@app.on_event("startup")
async def startup_event():
    """
    Inicializa conexões e configurações necessárias
    """
    # Conectar ao Redis
    await cache_manager.connect()
    
    # Conectar ao ClickHouse
    await clickhouse_client.connect()
    
    # Configurar processador de eventos
    await event_processor.setup()

@app.on_event("shutdown")
async def shutdown_event():
    """
    Fecha conexões ao encerrar a aplicação
    """
    await cache_manager.close()
    await clickhouse_client.close()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "analytics"} 