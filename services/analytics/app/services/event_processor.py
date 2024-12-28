from typing import Dict, Any
import json
from datetime import datetime
from app.core.clickhouse import clickhouse_client
from shared.messaging import message_broker

class EventProcessor:
    """
    Processa eventos recebidos via RabbitMQ e armazena no ClickHouse
    """
    
    def __init__(self):
        self.clickhouse = clickhouse_client
        self.event_handlers = {
            "content_generation": self._handle_content_generation,
            "content_created": self._handle_content_event,
            "content_updated": self._handle_content_event,
            "content_deleted": self._handle_content_event,
            "template_created": self._handle_template_event,
            "template_updated": self._handle_template_event,
            "template_deleted": self._handle_template_event,
            "template_used": self._handle_template_usage
        }
    
    async def setup(self):
        """
        Configura tabelas e consumidores
        """
        # Criar tabelas se não existirem
        await self._create_tables()
        
        # Configurar consumidores
        await message_broker.consume(
            "content_analytics",
            self.process_event
        )
        await message_broker.consume(
            "content_events",
            self.process_event
        )
        await message_broker.consume(
            "template_events",
            self.process_event
        )
    
    async def process_event(self, event: Dict[str, Any]):
        """
        Processa um evento recebido
        """
        try:
            event_type = event.get("event_type")
            if not event_type:
                raise ValueError("Evento sem tipo definido")
            
            handler = self.event_handlers.get(event_type)
            if not handler:
                raise ValueError(f"Tipo de evento não suportado: {event_type}")
            
            await handler(event)
            
        except Exception as e:
            # Em produção, enviar para sistema de monitoramento
            print(f"Erro ao processar evento: {str(e)}")
    
    async def _create_tables(self):
        """
        Cria tabelas necessárias no ClickHouse
        """
        # Tabela de eventos de geração de conteúdo
        await self.clickhouse.execute("""
            CREATE TABLE IF NOT EXISTS content_generation_events (
                timestamp DateTime,
                user_id UInt64,
                provider String,
                prompt_tokens UInt32,
                completion_tokens UInt32,
                cached UInt8,
                metadata String
            )
            ENGINE = MergeTree()
            ORDER BY (timestamp, user_id)
        """)
        
        # Tabela de eventos de conteúdo
        await self.clickhouse.execute("""
            CREATE TABLE IF NOT EXISTS content_events (
                timestamp DateTime,
                event_type String,
                content_id UInt64,
                user_id UInt64,
                content_type String,
                metadata String
            )
            ENGINE = MergeTree()
            ORDER BY (timestamp, user_id)
        """)
        
        # Tabela de eventos de template
        await self.clickhouse.execute("""
            CREATE TABLE IF NOT EXISTS template_events (
                timestamp DateTime,
                event_type String,
                template_id UInt64,
                user_id UInt64,
                template_type String,
                metadata String
            )
            ENGINE = MergeTree()
            ORDER BY (timestamp, user_id)
        """)
    
    async def _handle_content_generation(self, event: Dict[str, Any]):
        """
        Processa evento de geração de conteúdo
        """
        metadata = event.get("metadata", {})
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        
        await self.clickhouse.execute("""
            INSERT INTO content_generation_events (
                timestamp,
                user_id,
                provider,
                prompt_tokens,
                completion_tokens,
                cached,
                metadata
            ) VALUES
        """, [{
            "timestamp": datetime.fromisoformat(event["timestamp"]),
            "user_id": int(event["user_id"]),
            "provider": event["provider"],
            "prompt_tokens": metadata.get("prompt_tokens", 0),
            "completion_tokens": metadata.get("completion_tokens", 0),
            "cached": 1 if event.get("cached", False) else 0,
            "metadata": json.dumps(metadata)
        }])
    
    async def _handle_content_event(self, event: Dict[str, Any]):
        """
        Processa evento relacionado a conteúdo
        """
        metadata = event.get("metadata", {})
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        
        await self.clickhouse.execute("""
            INSERT INTO content_events (
                timestamp,
                event_type,
                content_id,
                user_id,
                content_type,
                metadata
            ) VALUES
        """, [{
            "timestamp": datetime.fromisoformat(event["timestamp"]),
            "event_type": event["event_type"],
            "content_id": event["content_id"],
            "user_id": event["user_id"],
            "content_type": metadata.get("content_type", "unknown"),
            "metadata": json.dumps(metadata)
        }])
    
    async def _handle_template_event(self, event: Dict[str, Any]):
        """
        Processa evento relacionado a template
        """
        metadata = event.get("metadata", {})
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        
        await self.clickhouse.execute("""
            INSERT INTO template_events (
                timestamp,
                event_type,
                template_id,
                user_id,
                template_type,
                metadata
            ) VALUES
        """, [{
            "timestamp": datetime.fromisoformat(event["timestamp"]),
            "event_type": event["event_type"],
            "template_id": event["template_id"],
            "user_id": event["user_id"],
            "template_type": metadata.get("template_type", "unknown"),
            "metadata": json.dumps(metadata)
        }])
    
    async def _handle_template_usage(self, event: Dict[str, Any]):
        """
        Processa evento de uso de template
        """
        metadata = event.get("metadata", {})
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        
        await self.clickhouse.execute("""
            INSERT INTO template_events (
                timestamp,
                event_type,
                template_id,
                user_id,
                template_type,
                metadata
            ) VALUES
        """, [{
            "timestamp": datetime.fromisoformat(event["timestamp"]),
            "event_type": "template_used",
            "template_id": event["template_id"],
            "user_id": event["user_id"],
            "template_type": metadata.get("template_type", "unknown"),
            "metadata": json.dumps({
                **metadata,
                "variables": event.get("variables", {}),
                "ai_provider": event.get("ai_provider"),
                "cached": event.get("cached", False)
            })
        }])

event_processor = EventProcessor() 