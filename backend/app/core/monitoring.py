import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def log_rate_limit_event(client_ip: str) -> None:
    """
    Registra um evento de rate limit.
    
    Args:
        client_ip: O IP do cliente que excedeu o limite
    """
    try:
        timestamp = datetime.utcnow().isoformat()
        logger.warning(f"Rate limit exceeded - IP: {client_ip} - Time: {timestamp}")
    except Exception as e:
        logger.error(f"Error logging rate limit event: {str(e)}") 