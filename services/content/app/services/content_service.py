from typing import Optional, List
from sqlalchemy.orm import Session
from openai import OpenAI
import json

from app.models.content import Content, ContentStatus
from app.models.generation import Generation
from app.schemas.content import ContentCreate, ContentUpdate
from app.core.config import settings

class ContentService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def get(self, db: Session, id: int) -> Optional[Content]:
        return db.query(Content).filter(Content.id == id).first()

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100, user_id: Optional[int] = None) -> List[Content]:
        query = db.query(Content)
        if user_id is not None:
            query = query.filter(Content.user_id == user_id)
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: ContentCreate) -> Content:
        db_obj = Content(
            title=obj_in.title,
            prompt=obj_in.prompt,
            parameters=json.dumps(obj_in.parameters) if obj_in.parameters else None,
            model=obj_in.model,
            user_id=obj_in.user_id,
            status=ContentStatus.PENDING
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: Content, obj_in: ContentUpdate) -> Content:
        update_data = obj_in.model_dump(exclude_unset=True)
        
        if "parameters" in update_data and update_data["parameters"]:
            update_data["parameters"] = json.dumps(update_data["parameters"])

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, id: int) -> Content:
        obj = db.query(Content).get(id)
        db.delete(obj)
        db.commit()
        return obj

    async def generate(self, db: Session, *, content: Content) -> Content:
        try:
            content.status = ContentStatus.GENERATING
            db.commit()

            # Criar uma nova geração
            generation = Generation(
                content_id=content.id,
                status="processing"
            )
            db.add(generation)
            db.commit()

            # Chamar a API da OpenAI
            response = await self.client.chat.completions.create(
                model=content.model or settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Você é um assistente especializado em gerar conteúdo de alta qualidade."},
                    {"role": "user", "content": content.prompt}
                ]
            )

            # Atualizar a geração com o resultado
            generation.result = response.choices[0].message.content
            generation.tokens_used = response.usage.total_tokens
            generation.cost = response.usage.total_tokens * 0.002 / 1000  # Custo aproximado
            generation.status = "completed"
            generation.generation_metadata = json.dumps(response.model_dump())

            # Atualizar o conteúdo
            content.result = response.choices[0].message.content
            content.status = ContentStatus.COMPLETED

            db.commit()
            return content

        except Exception as e:
            content.status = ContentStatus.FAILED
            if generation:
                generation.status = "failed"
                generation.error_message = str(e)
            db.commit()
            raise

content_service = ContentService() 