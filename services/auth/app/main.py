from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import auth, mfa, users
from app.core.config import settings

app = FastAPI(
    title="Auth Service",
    description="Serviço de autenticação e autorização",
    version="1.0.0"
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(mfa.router, prefix="/auth/mfa", tags=["mfa"])
app.include_router(users.router, prefix="/users", tags=["users"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "auth"} 