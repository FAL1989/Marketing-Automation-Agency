from typing import Dict, Any
from aio_pika import connect_robust, Message, ExchangeType
import json
from pydantic_settings import BaseSettings

class MessagingSettings(BaseSettings):
    RABBITMQ_URL: str
    
    class Config:
        env_file = ".env"

settings = MessagingSettings()

class MessageBroker:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchanges = {}
        self.queues = {}
    
    async def connect(self):
        """
        Estabelece conexão com o RabbitMQ e configura exchanges/filas
        """
        self.connection = await connect_robust(settings.RABBITMQ_URL)
        self.channel = await self.connection.channel()
        
        # Declarar exchanges
        self.exchanges["content"] = await self.channel.declare_exchange(
            "content",
            type=ExchangeType.TOPIC,
            durable=True
        )
        
        self.exchanges["analytics"] = await self.channel.declare_exchange(
            "analytics",
            type=ExchangeType.TOPIC,
            durable=True
        )
        
        # Declarar filas
        self.queues["content_generation"] = await self.channel.declare_queue(
            "content_generation",
            durable=True
        )
        
        self.queues["content_analytics"] = await self.channel.declare_queue(
            "content_analytics",
            durable=True
        )

        self.queues["content_events"] = await self.channel.declare_queue(
            "content_events",
            durable=True
        )

        self.queues["template_events"] = await self.channel.declare_queue(
            "template_events",
            durable=True
        )
        
        # Bindings
        await self.queues["content_generation"].bind(
            self.exchanges["content"],
            routing_key="content.generate"
        )
        
        await self.queues["content_analytics"].bind(
            self.exchanges["analytics"],
            routing_key="content.#"
        )

        await self.queues["content_events"].bind(
            self.exchanges["content"],
            routing_key="content.events.#"
        )

        await self.queues["template_events"].bind(
            self.exchanges["content"],
            routing_key="template.events.#"
        )
    
    async def publish_message(
        self,
        exchange: str,
        routing_key: str,
        message: Dict[str, Any],
        persistent: bool = True
    ):
        """
        Publica uma mensagem em um exchange específico
        """
        if not self.channel:
            await self.connect()
        
        message_bytes = json.dumps(message).encode()
        await self.exchanges[exchange].publish(
            Message(
                message_bytes,
                content_type="application/json",
                delivery_mode=2 if persistent else 1
            ),
            routing_key=routing_key
        )
    
    async def consume(self, queue_name: str, callback):
        """
        Consome mensagens de uma fila específica
        """
        if not self.channel:
            await self.connect()
        
        await self.queues[queue_name].consume(callback)
    
    async def close(self):
        """
        Fecha a conexão com o RabbitMQ
        """
        if self.connection:
            await self.connection.close()

message_broker = MessageBroker() 