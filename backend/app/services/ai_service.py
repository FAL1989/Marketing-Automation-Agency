from typing import Dict, Any, Optional
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from .providers import OpenAIProvider, AnthropicProvider, CohereProvider
from .ai_config_service import AIConfigService
from .queue_service import QueueService
from .rate_limiter import TokenBucketRateLimiter
from .monitoring_service import MonitoringService

logger = logging.getLogger(__name__)

class AIService:
    def __init__(
        self,
        config_service: AIConfigService,
        queue_service: QueueService,
        rate_limiter: TokenBucketRateLimiter,
        monitoring_service: MonitoringService
    ):
        """
        Inicializa o serviço de IA.
        
        Args:
            config_service: Serviço de configuração
            queue_service: Serviço de filas
            rate_limiter: Serviço de rate limiting
            monitoring_service: Serviço de monitoramento
        """
        self.config_service = config_service
        self.queue_service = queue_service
        self.rate_limiter = rate_limiter
        self.monitoring = monitoring_service
        
        # Inicializa os provedores
        self.providers = {
            "openai": OpenAIProvider(config_service),
            "anthropic": AnthropicProvider(config_service),
            "cohere": CohereProvider(config_service)
        }
        
    async def initialize(self):
        """Inicializa os workers de forma assíncrona"""
        await self._start_workers()
    
    async def _start_workers(self):
        """Inicia os workers para processar as filas de cada provedor"""
        for provider_name in self.providers:
            await self.queue_service.start_worker(
                f"ai_requests_{provider_name}",
                self._create_handler(provider_name),
                batch_size=5,
                polling_interval=1
            )
    
    def _create_handler(self, provider_name: str):
        """Cria um handler para processar itens da fila de um provedor"""
        async def handler(data: Dict[str, Any]):
            try:
                # Obtém o provedor
                provider = self.providers[provider_name]
                
                # Verifica o rate limit
                if not await self._check_rate_limit(provider_name):
                    raise Exception("Rate limit excedido")
                
                # Gera o conteúdo
                response = await provider.generate(
                    data["prompt"],
                    data["variables"],
                    data.get("model_name")
                )
                
                # Registra métricas
                self.monitoring.increment_counter(
                    "ai_requests_total",
                    {
                        "provider": provider_name,
                        "status": "success"
                    }
                )
                
                return response
                
            except Exception as e:
                logger.error(
                    f"Erro ao processar item para {provider_name}: {str(e)}"
                )
                self.monitoring.increment_counter(
                    "ai_requests_total",
                    {
                        "provider": provider_name,
                        "status": "error"
                    }
                )
                raise
                
        return handler
    
    async def _check_rate_limit(self, provider: str) -> bool:
        """Verifica o rate limit para um provedor"""
        limits = {
            "openai": (100, 1.0),  # 100 tokens/s
            "anthropic": (50, 0.5),  # 50 tokens/s
            "cohere": (20, 0.2)  # 20 tokens/s
        }
        
        capacity, refill_rate = limits[provider]
        return await self.rate_limiter.is_allowed(
            f"provider:{provider}",
            capacity,
            refill_rate
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate_content(
        self,
        prompt: str,
        variables: Dict[str, Any],
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        priority: int = 0
    ) -> str:
        """
        Gera conteúdo usando um provedor de IA.
        
        Args:
            prompt: O prompt base para geração
            variables: Variáveis para substituir no prompt
            provider: Nome do provedor a ser usado (opcional)
            model_name: Nome do modelo a ser usado (opcional)
            priority: Prioridade da requisição (0-9)
            
        Returns:
            str: O conteúdo gerado
            
        Raises:
            Exception: Se houver erro na geração
        """
        try:
            # Se não especificou provedor, escolhe o primeiro disponível
            if not provider:
                for name, p in self.providers.items():
                    if await p.validate_api_key():
                        provider = name
                        break
                if not provider:
                    raise Exception("Nenhum provedor disponível")
            
            # Verifica se o provedor existe
            if provider not in self.providers:
                raise ValueError(f"Provedor {provider} não encontrado")
            
            # Prepara os dados para a fila
            queue_data = {
                "prompt": prompt,
                "variables": variables,
                "model_name": model_name
            }
            
            # Enfileira a requisição
            item_id = await self.queue_service.enqueue(
                f"ai_requests_{provider}",
                queue_data,
                priority=priority
            )
            
            # Registra métricas
            self.monitoring.increment_counter(
                "ai_requests_total",
                {
                    "provider": provider,
                    "status": "queued"
                }
            )
            
            return item_id
            
        except Exception as e:
            logger.error(f"Erro ao gerar conteúdo: {str(e)}")
            self.monitoring.increment_counter(
                "ai_requests_total",
                {
                    "provider": provider if provider else "unknown",
                    "status": "error"
                }
            )
            raise
    
    async def get_request_status(
        self,
        item_id: str
    ) -> Dict[str, Any]:
        """
        Obtém o status de uma requisição.
        
        Args:
            item_id: ID do item na fila
            
        Returns:
            Dict: Status da requisição
        """
        try:
            # Extrai o nome da fila do ID
            queue_name = item_id.split(":")[0]
            
            # Verifica se o item ainda está na fila
            size = await self.queue_service.get_queue_size(queue_name)
            
            if size > 0:
                return {
                    "status": "pending",
                    "position": size
                }
            
            return {
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter status da requisição: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def close(self):
        """Fecha todas as conexões e para os workers"""
        # Para os workers
        for provider_name in self.providers:
            await self.queue_service.stop_worker(f"ai_requests_{provider_name}")
        
        # Fecha conexões
        await self.queue_service.close()
        await self.rate_limiter.close()