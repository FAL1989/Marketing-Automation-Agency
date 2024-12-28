from typing import Dict, Any, Optional
import httpx
from app.core.config import settings

class AIClient:
    """
    Cliente para comunicação com o AI Orchestrator
    """
    
    def __init__(self):
        self.base_url = "http://ai-orchestrator:8000/api/v1"
        self.client = httpx.AsyncClient(timeout=60.0)  # Timeout de 60 segundos
    
    async def generate_content(
        self,
        prompt: str,
        user_id: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Solicita geração de conteúdo ao AI Orchestrator
        """
        try:
            # Preparar payload
            payload = {
                "prompt": prompt,
                "provider": provider,
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # Remover campos None
            payload = {k: v for k, v in payload.items() if v is not None}
            
            # Fazer requisição
            response = await self.client.post(
                f"{self.base_url}/generate",
                json=payload,
                headers={"X-User-Id": str(user_id)}
            )
            
            # Verificar resposta
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            raise Exception(f"Erro na comunicação com AI Orchestrator: {str(e)}")
        except Exception as e:
            raise Exception(f"Erro ao gerar conteúdo: {str(e)}")
    
    async def get_usage_stats(
        self,
        user_id: str,
        provider: str
    ) -> Dict[str, Any]:
        """
        Obtém estatísticas de uso do provedor
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/usage/{provider}",
                headers={"X-User-Id": str(user_id)}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"Erro na comunicação com AI Orchestrator: {str(e)}")
        except Exception as e:
            raise Exception(f"Erro ao obter estatísticas: {str(e)}")
    
    async def close(self):
        """
        Fecha o cliente HTTP
        """
        await self.client.aclose()

ai_client = AIClient() 