import json
import pika
from typing import Dict, Any
from app.core.config import settings

def get_connection():
    """
    Cria uma conexão com o RabbitMQ
    """
    parameters = pika.URLParameters(settings.RABBITMQ_URL)
    return pika.BlockingConnection(parameters)

def publish_message(exchange: str, routing_key: str, message: Dict[str, Any]) -> None:
    """
    Publica uma mensagem no RabbitMQ
    """
    connection = get_connection()
    channel = connection.channel()
    
    # Declarar exchange
    channel.exchange_declare(
        exchange=exchange,
        exchange_type='topic',
        durable=True
    )
    
    # Publicar mensagem
    channel.basic_publish(
        exchange=exchange,
        routing_key=routing_key,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,  # Mensagem persistente
            content_type='application/json'
        )
    )
    
    connection.close()

def setup_rabbitmq():
    """
    Configura as exchanges e filas necessárias
    """
    connection = get_connection()
    channel = connection.channel()
    
    # Declarar exchanges
    channel.exchange_declare(
        exchange='content',
        exchange_type='topic',
        durable=True
    )
    
    # Declarar filas
    channel.queue_declare(
        queue='content_generation',
        durable=True
    )
    
    # Bind filas às exchanges
    channel.queue_bind(
        exchange='content',
        queue='content_generation',
        routing_key='content.generate'
    )
    
    connection.close() 