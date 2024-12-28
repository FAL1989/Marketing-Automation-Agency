from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.content import Content
from app.schemas.content import ContentCreate, ContentUpdate
from app.services.ai_client import ai_client
from shared.messaging import message_broker

class ContentService:
    async def create_content(
        self,
        db: Session,
        user_id: int,
        content_data: ContentCreate
    ) -> Content:
        """
        Cria novo conteúdo, gerando texto via AI se necessário
        """
        # Se prompt fornecido, gerar conteúdo via AI
        if content_data.prompt:
            try:
                # Gerar conteúdo
                result = await ai_client.generate_content(
                    prompt=content_data.prompt,
                    user_id=str(user_id),
                    provider=content_data.ai_provider,
                    model=content_data.ai_model,
                    temperature=content_data.temperature,
                    max_tokens=content_data.max_tokens
                )
                
                # Atualizar texto com conteúdo gerado
                content_data.text = result["content"]
                content_data.content_metadata = {
                    "ai_provider": result["source"],
                    "cached": result["cached"],
                    "prompt": content_data.prompt
                }
            except Exception as e:
                raise Exception(f"Erro ao gerar conteúdo: {str(e)}")
        
        # Criar objeto de conteúdo
        db_content = Content(
            user_id=user_id,
            title=content_data.title,
            text=content_data.text,
            content_type=content_data.content_type,
            content_metadata=content_data.content_metadata
        )
        
        try:
            # Salvar no banco
            db.add(db_content)
            db.commit()
            db.refresh(db_content)
            
            # Publicar evento de criação
            await self._publish_content_event(
                "content_created",
                db_content.id,
                user_id
            )
            
            return db_content
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao salvar conteúdo: {str(e)}")
    
    def get_content(
        self,
        db: Session,
        content_id: int,
        user_id: int
    ) -> Optional[Content]:
        """
        Obtém conteúdo por ID
        """
        return db.query(Content).filter(
            Content.id == content_id,
            Content.user_id == user_id
        ).first()
    
    def list_contents(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Content]:
        """
        Lista conteúdos do usuário
        """
        return db.query(Content).filter(
            Content.user_id == user_id
        ).offset(skip).limit(limit).all()
    
    async def update_content(
        self,
        db: Session,
        content_id: int,
        user_id: int,
        content_data: ContentUpdate
    ) -> Optional[Content]:
        """
        Atualiza conteúdo existente
        """
        db_content = self.get_content(db, content_id, user_id)
        if not db_content:
            return None
        
        try:
            # Se prompt fornecido, gerar novo conteúdo
            if content_data.prompt:
                result = await ai_client.generate_content(
                    prompt=content_data.prompt,
                    user_id=str(user_id),
                    provider=content_data.ai_provider,
                    model=content_data.ai_model,
                    temperature=content_data.temperature,
                    max_tokens=content_data.max_tokens
                )
                
                content_data.text = result["content"]
                content_data.content_metadata = {
                    "ai_provider": result["source"],
                    "cached": result["cached"],
                    "prompt": content_data.prompt
                }
            
            # Atualizar campos
            for field, value in content_data.dict(exclude_unset=True).items():
                setattr(db_content, field, value)
            
            # Salvar alterações
            db.commit()
            db.refresh(db_content)
            
            # Publicar evento de atualização
            await self._publish_content_event(
                "content_updated",
                content_id,
                user_id
            )
            
            return db_content
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao atualizar conteúdo: {str(e)}")
    
    async def delete_content(
        self,
        db: Session,
        content_id: int,
        user_id: int
    ) -> bool:
        """
        Remove conteúdo existente
        """
        db_content = self.get_content(db, content_id, user_id)
        if not db_content:
            return False
        
        try:
            # Remover do banco
            db.delete(db_content)
            db.commit()
            
            # Publicar evento de remoção
            await self._publish_content_event(
                "content_deleted",
                content_id,
                user_id
            )
            
            return True
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao remover conteúdo: {str(e)}")
    
    async def _publish_content_event(
        self,
        event_type: str,
        content_id: int,
        user_id: int
    ):
        """
        Publica evento relacionado a conteúdo
        """
        event = {
            "event_type": event_type,
            "content_id": content_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await message_broker.publish(
            "content_events",
            event
        )

content_service = ContentService() 