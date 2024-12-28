import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from ..models.content import Content
from ..models.generation import Generation
from ..database.connection import get_db
from core.ai.orchestrator import AIOrchestrator

logger = logging.getLogger(__name__)

class ContentService:
    def __init__(self):
        self.ai_orchestrator = AIOrchestrator()

    async def create_content(self, db: Session, user_id: int, title: str, prompt: str, 
                           parameters: Optional[Dict[str, Any]] = None, 
                           model: str = "gpt-3.5-turbo") -> Content:
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
        try:
            content = db.query(Content).filter(Content.id == content_id).first()
            if not content:
                raise HTTPException(status_code=404, detail="Content not found")

            # Atualiza o status para "generating"
            content.status = "generating"
            db.commit()

            try:
                # Usa o AIOrchestrator para gerar o conteúdo
                response = await self.ai_orchestrator.generate_content(
                    prompt=content.prompt,
                    user_id=str(content.user_id),
                    provider=content.parameters.get("provider", "openai"),
                    model=content.model,
                    **content.parameters
                )

                # Cria um novo registro de geração
                generation = Generation(
                    content_id=content.id,
                    template_id=template_id,
                    result=response["content"],
                    tokens_used=response.get("tokens_used"),
                    cost=response.get("cost"),
                    status="completed",
                    generation_metadata={
                        "source": response["source"],
                        "cached": response["cached"]
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