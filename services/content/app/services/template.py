from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.template import Template
from app.schemas.template import TemplateCreate, TemplateUpdate, TemplateUse
from app.services.content import content_service
from app.services.ai_client import ai_client
from shared.messaging import message_broker

class TemplateService:
    async def create_template(
        self,
        db: Session,
        user_id: int,
        template_data: TemplateCreate
    ) -> Template:
        """
        Cria novo template
        """
        try:
            # Criar objeto de template
            db_template = Template(
                user_id=user_id,
                name=template_data.name,
                description=template_data.description,
                template_type=template_data.template_type,
                prompt_template=template_data.prompt_template,
                default_params=template_data.default_params,
                template_metadata=template_data.template_metadata
            )
            
            # Salvar no banco
            db.add(db_template)
            db.commit()
            db.refresh(db_template)
            
            # Publicar evento de criação
            await self._publish_template_event(
                "template_created",
                db_template.id,
                user_id
            )
            
            return db_template
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao criar template: {str(e)}")
    
    def get_template(
        self,
        db: Session,
        template_id: int,
        user_id: int
    ) -> Optional[Template]:
        """
        Obtém template por ID
        """
        return db.query(Template).filter(
            Template.id == template_id,
            Template.user_id == user_id
        ).first()
    
    def list_templates(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Template]:
        """
        Lista templates do usuário
        """
        return db.query(Template).filter(
            Template.user_id == user_id
        ).offset(skip).limit(limit).all()
    
    async def update_template(
        self,
        db: Session,
        template_id: int,
        user_id: int,
        template_data: TemplateUpdate
    ) -> Optional[Template]:
        """
        Atualiza template existente
        """
        db_template = self.get_template(db, template_id, user_id)
        if not db_template:
            return None
        
        try:
            # Atualizar campos
            for field, value in template_data.dict(exclude_unset=True).items():
                setattr(db_template, field, value)
            
            # Salvar alterações
            db.commit()
            db.refresh(db_template)
            
            # Publicar evento de atualização
            await self._publish_template_event(
                "template_updated",
                template_id,
                user_id
            )
            
            return db_template
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao atualizar template: {str(e)}")
    
    async def delete_template(
        self,
        db: Session,
        template_id: int,
        user_id: int
    ) -> bool:
        """
        Remove template existente
        """
        db_template = self.get_template(db, template_id, user_id)
        if not db_template:
            return False
        
        try:
            # Remover do banco
            db.delete(db_template)
            db.commit()
            
            # Publicar evento de remoção
            await self._publish_template_event(
                "template_deleted",
                template_id,
                user_id
            )
            
            return True
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao remover template: {str(e)}")
    
    async def use_template(
        self,
        db: Session,
        user_id: int,
        template_use: TemplateUse
    ) -> Dict[str, Any]:
        """
        Usa um template para gerar conteúdo
        """
        # Obter template
        db_template = self.get_template(
            db,
            template_use.template_id,
            user_id
        )
        if not db_template:
            raise Exception("Template não encontrado")
        
        try:
            # Mesclar variáveis com padrões
            variables = {
                **db_template.default_params,
                **template_use.variables
            }
            
            # Gerar prompt
            try:
                prompt = db_template.prompt_template.format(**variables)
            except KeyError as e:
                raise Exception(f"Variável obrigatória não fornecida: {str(e)}")
            
            # Gerar conteúdo via AI
            result = await ai_client.generate_content(
                prompt=prompt,
                user_id=str(user_id),
                provider=template_use.ai_provider,
                model=template_use.ai_model,
                temperature=template_use.temperature,
                max_tokens=template_use.max_tokens
            )
            
            # Criar conteúdo
            content = await content_service.create_content(
                db=db,
                user_id=user_id,
                content_data={
                    "title": f"[{db_template.name}] {variables.get('title', 'Sem título')}",
                    "text": result["content"],
                    "content_type": db_template.template_type,
                    "template_metadata": {
                        "template_id": db_template.id,
                        "variables": variables,
                        "ai_provider": result["source"],
                        "cached": result["cached"],
                        "prompt": prompt
                    }
                }
            )
            
            return {
                "content_id": content.id,
                "content": content.text,
                "source": result["source"],
                "cached": result["cached"]
            }
            
        except Exception as e:
            raise Exception(f"Erro ao usar template: {str(e)}")
    
    async def _publish_template_event(
        self,
        event_type: str,
        template_id: int,
        user_id: int
    ):
        """
        Publica evento relacionado a template
        """
        event = {
            "event_type": event_type,
            "template_id": template_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await message_broker.publish(
            "template_events",
            event
        )

template_service = TemplateService() 