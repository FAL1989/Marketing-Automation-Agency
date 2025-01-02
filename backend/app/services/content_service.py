import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException
from ..models.content import Content
from ..models.generation import Generation
from ..db.deps import get_db
from .ai_service import AIService
from .ai_config_service import AIConfigService
from .queue_service import QueueService
from .rate_limiter import TokenBucketRateLimiter
from .monitoring_service import MonitoringService
from ..core.config import settings
import asyncio

logger = logging.getLogger(__name__)

class ContentService:
    _instance = None
    _initialized = False
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_init'):
            self.monitoring_service = None
            self.config_service = None
            self.queue_service = None
            self.rate_limiter = None
            self.ai_service = None
            self._init = True

    async def initialize(self):
        """Inicializa os serviços de forma assíncrona"""
        try:
            self.monitoring_service = MonitoringService()
            self.config_service = AIConfigService()
            self.queue_service = QueueService(
                redis_url=settings.REDIS_URL,
                monitoring_service=self.monitoring_service
            )
            self.rate_limiter = TokenBucketRateLimiter(settings.REDIS_URL)
            self.ai_service = AIService(
                self.config_service,
                self.queue_service,
                self.rate_limiter,
                self.monitoring_service
            )
            await self.ai_service.initialize()
            ContentService._initialized = True
            logger.info("ContentService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ContentService: {str(e)}")
            ContentService._initialized = False
            raise

    async def ensure_initialized(self):
        """Garante que os serviços estão inicializados de forma thread-safe"""
        if not ContentService._initialized:
            async with self._lock:
                if not ContentService._initialized:
                    await self.initialize()

    async def create_content(self, db: Session, user_id: int, title: str, prompt: str, 
                           parameters: Optional[Dict[str, Any]] = None, 
                           model: str = "gpt-3.5-turbo") -> Content:
        await self.ensure_initialized()
        try:
            content = Content(
                title=title,
                prompt=prompt,
                parameters=parameters or {},
                model=model,
                user_id=user_id,
                status="pending"
            )
            db.add(content)
            db.commit()
            db.refresh(content)
            return content
        except Exception as e:
            logger.error(f"Error creating content: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error creating content: {str(e)}")

    async def generate_content(self, db: Session, content_id: int, template_id: int = None) -> Content:
        await self.ensure_initialized()
        try:
            content = db.query(Content).filter(Content.id == content_id).first()
            if not content:
                raise HTTPException(status_code=404, detail="Content not found")

            # Atualiza o status para "generating"
            content.status = "generating"
            db.commit()

            try:
                # Usa o AIService para gerar o conteúdo
                item_id = await self.ai_service.generate_content(
                    prompt=content.prompt,
                    variables={"user_id": str(content.user_id)},
                    provider=content.parameters.get("provider", "openai"),
                    model_name=content.model
                )

                # Aguarda o resultado
                status = await self.ai_service.get_request_status(item_id)
                if status["status"] == "error":
                    raise Exception(status.get("error", "Unknown error"))

                # Cria um novo registro de geração
                generation = Generation(
                    content_id=content.id,
                    template_id=template_id,
                    result=status.get("content", ""),
                    tokens_used=status.get("tokens_used"),
                    cost=status.get("cost"),
                    status="completed",
                    generation_metadata={
                        "source": status.get("provider"),
                        "cached": status.get("cached", False)
                    }
                )
                db.add(generation)

                # Atualiza o status do conteúdo
                content.status = "completed"
                content.result = generation.result
                db.commit()
                db.refresh(content)
                return content

            except Exception as e:
                logger.error(f"Error in content generation: {str(e)}")
                # Cria um registro de geração com erro
                generation = Generation(
                    content_id=content.id,
                    template_id=template_id,
                    error_message=str(e),
                    status="error"
                )
                db.add(generation)
                content.status = "error"
                db.commit()
                raise

        except Exception as e:
            logger.error(f"Error in generate_content: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_content(self, db: Session, content_id: int) -> Content:
        await self.ensure_initialized()
        try:
            content = db.query(Content).filter(Content.id == content_id).first()
            if not content:
                raise HTTPException(status_code=404, detail="Content not found")
            return content
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Error getting content: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error getting content: {str(e)}")

    async def list_contents(self, db: Session, user_id: Optional[int] = None, 
                          skip: int = 0, limit: int = 10) -> list[Content]:
        await self.ensure_initialized()
        try:
            query = db.query(Content)
            if user_id:
                query = query.filter(Content.user_id == user_id)
            return query.offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error listing contents: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error listing contents: {str(e)}")

    async def update_content(self, db: Session, content_id: int, 
                           title: Optional[str] = None, 
                           prompt: Optional[str] = None,
                           parameters: Optional[Dict[str, Any]] = None) -> Content:
        await self.ensure_initialized()
        try:
            content = db.query(Content).filter(Content.id == content_id).first()
            if not content:
                raise HTTPException(status_code=404, detail="Content not found")
            
            if title:
                content.title = title
            if prompt:
                content.prompt = prompt
            if parameters:
                content.parameters = parameters
            
            db.commit()
            db.refresh(content)
            return content
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Error updating content: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error updating content: {str(e)}")

    async def delete_content(self, db: Session, content_id: int) -> bool:
        await self.ensure_initialized()
        try:
            content = db.query(Content).filter(Content.id == content_id).first()
            if not content:
                raise HTTPException(status_code=404, detail="Content not found")
            
            db.delete(content)
            db.commit()
            return True
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Error deleting content: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error deleting content: {str(e)}")

    async def __del__(self):
        """Cleanup resources"""
        if self.ai_service:
            try:
                await self.ai_service.close()
            except Exception as e:
                logger.error(f"Error closing AI service: {str(e)}") 